"""Coordinator-owned ephemeral speech attempts; raw PCM never enters storage/logs."""

import asyncio
from dataclasses import dataclass, field
import json
import secrets
from time import monotonic

from fastapi import HTTPException, WebSocketDisconnect
from backend.defense_session import MAX_ANSWER_CHARS
from backend.resource_limits import Capacity, RateLimit, limit
from backend import speech_provider

RATE = speech_provider.RATE
def allowance():
    return RATE * limit('VOICE_ALLOWANCE_SECONDS', 600, 600)
capacity = Capacity()
starts = RateLimit()


@dataclass
class Transcript:
    previous: dict[str, str | None] = field(default_factory=dict)
    final: dict[str, str] = field(default_factory=dict)
    partial: dict[str, str] = field(default_factory=dict)
    seen: set[str] = field(default_factory=set)

    def receive(self, event):
        kind, item = event.get('type'), event.get('item_id')
        if kind in {'error', 'conversation.item.input_audio_transcription.failed'}:
            raise ValueError('Speech recognition failed. Nothing was submitted; use typing or record again.')
        if kind not in {'input_audio_buffer.committed', 'conversation.item.input_audio_transcription.delta', 'conversation.item.input_audio_transcription.completed'}:
            return
        if not isinstance(item, str) or not 1 <= len(item) <= 128:
            raise ValueError('Invalid speech segment. Use typing.')
        identity = event.get('event_id')
        if identity:
            if not isinstance(identity, str) or len(identity) > 128:
                raise ValueError("Invalid speech event identity. Use typing.")
            if identity in self.seen:
                return
            if len(self.seen) >= 4096:
                raise ValueError('Speech event limit reached. Use typing.')
            self.seen.add(identity)
        if len(set(self.previous) | set(self.final) | set(self.partial) | {item}) > 128:
            raise ValueError('Speech segment limit reached. Use typing.')
        if kind == 'input_audio_buffer.committed':
            previous = event.get('previous_item_id')
            if previous is not None and (not isinstance(previous, str) or len(previous) > 128):
                raise ValueError('Invalid speech order. Use typing.')
            if item in self.previous and self.previous[item] != previous:
                raise ValueError('Conflicting speech order. Use typing.')
            self.previous[item] = previous
        elif kind.endswith('.completed'):
            text = event.get('transcript')
            if not isinstance(text, str) or item in self.final and self.final[item] != text:
                raise ValueError('Invalid final transcript. Use typing.')
            self.final[item] = text
            self.partial.pop(item, None)
        elif item not in self.final:
            delta = event.get('delta')
            if not isinstance(delta, str):
                raise ValueError('Invalid speech text. Use typing.')
            self.partial[item] = self.partial.get(item, '') + delta
        if sum(map(len, self.final.values())) + sum(map(len, self.partial.values())) > MAX_ANSWER_CHARS:
            raise ValueError('The spoken answer exceeds 4000 characters. Nothing was submitted; record a shorter answer or type.')

    def ordered(self):
        ordered, previous = [], None
        for _ in self.previous:
            following = [item for item, before in self.previous.items() if before == previous]
            if len(following) != 1 or following[0] in ordered:
                return []
            previous = following[0]
            ordered.append(previous)
        return ordered

    def text(self, final_only=False):
        order = self.ordered()
        if not final_only:
            order += [item for item in self.partial if item not in order]
        text = ' '.join(self.final.get(item, '' if final_only else self.partial.get(item, '')) for item in order).strip()
        if len(text) > MAX_ANSWER_CHARS:
            raise ValueError('The spoken answer exceeds 4000 characters. Record a shorter answer or type.')
        return text


@dataclass
class SpeechAttempt:
    token: str
    run_id: str
    turn: int
    view_id: str
    task: asyncio.Task
    probe_id: str | None = None
    interpretation_id: int = 0
    id: str = field(default_factory=lambda: secrets.token_hex(24))
    transcript: Transcript = field(default_factory=Transcript)
    status: str = 'starting'
    children: list[asyncio.Task] = field(default_factory=list, repr=False)
    padding_samples: int = 0
    frames: int = 0
    last_published: float = 0
    samples: int = 0
    buffered: int = 0
    commits: int = 0
    started: float = field(default_factory=lambda: monotonic())
    finalizing_at: float | None = None


@dataclass(frozen=True)
class FinalizedDraft:
    token: str
    run_id: str
    turn: int
    view_id: str
    probe_id: str | None
    interpretation_id: int
    id: str
    text: str
    provenance: dict


@dataclass
class SpeechState:
    run_id: str | None = None
    used: int = 0
    attempts: int = 0
    current: SpeechAttempt | None = None
    draft: FinalizedDraft | None = None

    def reset(self, run_id):
        self.revoke()
        self.run_id, self.used, self.attempts = run_id, 0, 0

    def revoke(self, *, preserve_draft=False):
        if not preserve_draft:
            self.draft = None
        current, self.current = self.current, None
        if current:
            current.status = 'stopped'
            for child in current.children:
                if child is not asyncio.current_task():
                    child.cancel()
            if current.task is not asyncio.current_task():
                current.task.cancel()

    def snapshot(self):
        return {'enabled': speech_provider.configured(), 'remaining_ms': max(0, (allowance() - self.used) * 1000 // RATE),
                'provider': 'OpenAI', 'model': speech_provider.MODEL, 'language': 'en'}


def current_probe_id(room):
    if room.defense and room.defense.turns:
        probe = room.defense.turns[-1].probe
        if probe and probe.status == "pending":
            return probe.id
    return None


def scope_current(room, scope, now):
    player = room.players.get(scope.token)
    return (not room.closed and speech_provider.configured()
        and room.run_id == scope.run_id and room.defense_view_id == scope.view_id
        and room.defense_type in {'research', 'mixed'}
        and (room.phase in {'question', 'probe', 'interpretation_retry'}
             or room.phase == 'interpreting' and (room.pause_deadline_ms is None or now >= room.pause_deadline_ms))
        and room.defense is not None and len(room.defense.turns) - 1 == scope.turn
        and room.interpretation_id == scope.interpretation_id
        and scope.probe_id == current_probe_id(room)
        and player is not None and bool(player.sockets) and player.seat == room.selected_seat
        and room.answer_deadline_ms is not None and now < room.answer_deadline_ms)


def authorized(owner, attempt):
    return owner._room.speech.current is attempt and scope_current(owner._room, attempt, owner._workflows.now())


def draft_snapshot(room, recipient, now):
    draft = room.speech.draft
    if draft and recipient and recipient.token == draft.token and scope_current(room, draft, now):
        return {'attempt_id': draft.id, 'text': draft.text, 'turn': draft.turn,
                'probe_id': draft.probe_id, 'view_id': draft.view_id}
    return None


def revoke_obsolete(owner):
    room = owner._room
    draft = room.speech.draft
    if draft and not scope_current(room, draft, owner._workflows.now()):
        room.speech.draft = None
    attempt = room.speech.current
    if attempt and not authorized(owner, attempt):
        room.speech.revoke(preserve_draft=True)


def validate_submission(owner, actor, turn, text, attempt_id, probe_id=None):
    draft = owner._room.speech.draft
    if (draft is None or draft.id != attempt_id or draft.token != actor.token or draft.turn != turn
            or draft.probe_id != probe_id or not scope_current(owner._room, draft, owner._workflows.now())
            or text != draft.text or not text):
        raise ValueError('This voice draft is not a current finalized answer. Nothing was accepted; use typing or record again.')
    return dict(draft.provenance)


def ready_event(room, attempt):
    order = attempt.transcript.ordered()
    if (attempt.status == 'finalizing' and attempt.commits > 0 and len(order) == attempt.commits
            and all(item in attempt.transcript.final for item in order)):
        text = attempt.transcript.text(True)
        if not text:
            raise ValueError('No speech was recognized. Nothing was submitted; record again or type.')
        attempt.status = 'ready'
        room.speech.draft = FinalizedDraft(attempt.token, attempt.run_id, attempt.turn, attempt.view_id,
            attempt.probe_id, attempt.interpretation_id, attempt.id, text,
            {'method': 'voice', 'provider': 'OpenAI', 'model': speech_provider.MODEL,
             'audio_ms': attempt.samples * 1000 // RATE, 'padding_ms': attempt.padding_samples * 1000 // RATE})
        room.revision += 1
        return {'type': 'ready', 'attempt_id': attempt.id, 'text': text}
    return None


async def run_speech(owner, actor, socket, hello):
    room = owner._room
    attempt = None
    acquired = False
    async def send(event):
        await asyncio.wait_for(socket.send_json(event), 1)
    try:
        async with room.lock:
            player = owner._player(actor)
            if room.speech.run_id != room.run_id:
                room.speech.reset(room.run_id)
            if room.speech.current is not None:
                raise ValueError('A voice attempt is already active. Stop it before recording again.')
            attempt = SpeechAttempt(actor.token, room.run_id, hello.get('turn'), hello.get('view_id'), asyncio.current_task(), probe_id=hello.get('probe_id'), interpretation_id=room.interpretation_id)
            room.speech.current = attempt
            if type(attempt.turn) is not int or not authorized(owner, attempt):
                room.speech.current = None
                raise ValueError('Only the current chosen defender can start voice for this research answer. Use typing if voice is unavailable.')
            if room.speech.used >= allowance() or room.speech.attempts >= limit('VOICE_ATTEMPTS_PER_RUN', 40, 80):
                raise ValueError('Voice allowance or attempts used. Typing remains available.')
            starts.admit(room.owner_account_id, 12)
            capacity.acquire(room.owner_account_id, limit('VOICE_MAX_STREAMS', 16, 64), 1)
            acquired = True
            room.speech.draft = None
            room.speech.attempts += 1
            owner._retain(attempt.task)
        async with speech_provider.open_transcription(room.owner_account_id) as upstream:
            async with room.lock:
                if not authorized(owner, attempt):
                    raise ValueError('Voice authorization ended. Nothing was submitted.')
                attempt.status = 'listening'
            await send({'type': 'started', 'attempt_id': attempt.id, **room.speech.snapshot()})
            async def forward(events):
                # No await between the last authorization check and beginning IO.
                # Revocation directly cancels these children, including blocked writes.
                for payload in events:
                    if not authorized(owner, attempt):
                        raise ValueError('Voice authorization ended. Nothing was submitted.')
                    await asyncio.wait_for(upstream.send(payload), .5)

            async def client_events():
                while True:
                    event = await socket.receive()
                    if event['type'] == 'websocket.disconnect':
                        raise WebSocketDisconnect()
                    frame = event.get('bytes')
                    if frame is not None:
                        if not 2 <= len(frame) <= 9600 or len(frame) % 2:
                            raise ValueError('Invalid audio frame. Nothing was submitted; use typing.')
                        async with room.lock:
                            if not authorized(owner, attempt):
                                raise ValueError('Voice authorization ended. Nothing was submitted.')
                            attempt.frames += 1
                            if attempt.frames > (monotonic() - attempt.started + .5) * 60 + 1:
                                raise ValueError("Audio frame rate exceeded. Nothing was submitted; use typing.")
                            if room.speech.used >= allowance() and attempt.status in {'finalizing', 'ready'}:
                                # A bounded in-flight frame can precede the browser's cap notification.
                                # It must not cancel the already-paid finalization or be forwarded.
                                continue
                            if attempt.status != 'listening':
                                raise ValueError('This voice attempt is no longer recording.')
                            samples = len(frame) // 2
                            if attempt.samples + samples > (monotonic() - attempt.started + .5) * RATE:
                                raise ValueError('Audio arrived faster than real time. Nothing was submitted.')
                            events = []
                            remaining = allowance() - room.speech.used
                            frame = frame[:remaining * 2]
                            if frame:
                                # Reserve before IO: uncertain failed sends count conservatively, never exceed cap.
                                room.speech.used += len(frame) // 2
                                attempt.samples += len(frame) // 2
                                attempt.buffered += len(frame) // 2
                                events.append(speech_provider.audio_event(frame))
                            if attempt.buffered >= RATE * 2:
                                events.append(commit_event(attempt))
                            capped = room.speech.used >= allowance()
                            if capped:
                                events.extend(finish_events(room, attempt))
                            publish_usage = capped or monotonic() - attempt.last_published >= 1
                            if publish_usage:
                                attempt.last_published = monotonic()
                                room.revision += 1
                        await forward(events)
                        await send({'type': 'allowance', 'capped': capped, **room.speech.snapshot()})
                        if publish_usage:
                            await owner._publish()
                    else:
                        raw = event.get('text', '')
                        if len(raw) > 200:
                            raise ValueError('Invalid speech control.')
                        control = json.loads(raw).get('type')
                        if control == 'cancel':
                            async with room.lock:
                                if room.speech.draft and room.speech.draft.id == attempt.id:
                                    room.speech.draft = None
                            return
                        if control != 'finalize':
                            raise ValueError('Invalid speech control.')
                        async with room.lock:
                            if not authorized(owner, attempt) or attempt.status not in {'listening', 'finalizing', 'ready'}:
                                raise ValueError('This voice attempt has ended.')
                            events = finish_events(room, attempt) if attempt.status == 'listening' else []
                        await forward(events)
                        async with room.lock:
                            if not authorized(owner, attempt):
                                raise ValueError('Voice authorization ended. Nothing was submitted.')
                            finalized = ready_event(room, attempt)
                        await send(finalized or {'type': 'finalizing'})
                        if finalized:
                            await owner._publish()
            async def provider_events():
                for _ in range(4096):
                    event = json.loads(await upstream.recv())
                    async with room.lock:
                        if not authorized(owner, attempt):
                            raise ValueError('Voice authorization ended. Nothing was submitted.')
                        attempt.transcript.receive(event)
                        outgoing = ready_event(room, attempt) or {'type': 'transcript', 'text': attempt.transcript.text(),
                            'finalized_text': attempt.transcript.text(True)}
                    await send(outgoing)
                    if outgoing['type'] == 'ready':
                        await owner._publish()
                raise ValueError('Speech event limit reached. Use typing.')
            async def watchdog():
                while True:
                    await asyncio.sleep(.1)
                    async with room.lock:
                        if not authorized(owner, attempt):
                            raise ValueError('Voice window ended. Nothing was submitted; use the current answer controls.')
                        if attempt.finalizing_at is not None and attempt.status == 'finalizing' and monotonic() - attempt.finalizing_at > 8:
                            raise ValueError('Transcript finalization timed out. Nothing was submitted; use typing.')
                        if monotonic() - attempt.started > 125:
                            raise ValueError('Voice attempt time limit reached. Nothing was submitted; use typing.')
            tasks = [asyncio.create_task(job()) for job in (client_events, provider_events, watchdog)]
            attempt.children = tasks
            try:
                done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    task.result()
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
    except asyncio.CancelledError:
        try:
            await send({'type': 'stopped', 'message': 'Voice capture stopped. Nothing was submitted automatically.'})
        except Exception:
            pass
    except (ValueError, HTTPException) as error:
        await send({'type': 'error', 'message': str(error.detail) if isinstance(error, HTTPException) else str(error)})
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await send({'type': 'error', 'message': 'Speech service unavailable. Nothing was submitted; use typing or record again.'})
        except Exception:
            pass
    finally:
        async with room.lock:
            if attempt is not None and room.speech.current is attempt:
                room.speech.current = None
        if acquired:
            capacity.release(room.owner_account_id)
        try:
            await asyncio.wait_for(socket.close(), 1)
        except Exception:
            pass


def commit_event(attempt):
    if not attempt.buffered:
        raise ValueError('There is no audio to finalize.')
    attempt.commits += 1
    attempt.buffered = 0
    return json.dumps({'type': 'input_audio_buffer.commit'})


def finish_events(room, attempt):
    events = []
    if 0 < attempt.buffered < RATE // 10:
        padding = RATE // 10 - attempt.buffered
        if room.speech.used + padding > allowance():
            raise ValueError('The voice cap left a segment too short to finalize. Nothing was submitted; use typing.')
        room.speech.used += padding
        attempt.samples += padding
        attempt.padding_samples += padding
        attempt.buffered += padding
        events.append(speech_provider.audio_event(bytes(padding * 2)))
    if attempt.buffered:
        events.append(commit_event(attempt))
    if attempt.commits == 0:
        raise ValueError('Record an answer before sending. Nothing was submitted.')
    attempt.status = 'finalizing'
    attempt.finalizing_at = monotonic()
    return events
