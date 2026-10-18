"""OpenAI-only live transcription IO. Text-model routing never supplies this key."""

import base64
from contextlib import asynccontextmanager
import hashlib
import json
import os
import asyncio
from websockets.asyncio import client

MODEL = 'gpt-live-transcribe'
RATE = 24_000


def configured() -> bool:
    return (os.getenv('VOICE_PILOT_ENABLED') == '1' and bool(os.getenv('OPENAI_SPEECH_API_KEY'))
            and os.getenv('OPENAI_SPEECH_MODEL', MODEL) == MODEL)


@asynccontextmanager
async def open_transcription(owner_id: str):
    if not configured():
        raise ValueError('Voice practice is unavailable. Use typing.')
    async with client.connect('wss://api.openai.com/v1/realtime?intent=transcription',
            additional_headers={'Authorization': f"Bearer {os.environ['OPENAI_SPEECH_API_KEY']}",
                'OpenAI-Safety-Identifier': hashlib.sha256(owner_id.encode()).hexdigest()},
            max_size=32768, max_queue=8, open_timeout=5, close_timeout=1) as socket:
        session = {'type': 'transcription', 'audio': {'input': {
            'format': {'type': 'audio/pcm', 'rate': RATE},
            'transcription': {'model': MODEL, 'languages': ['en']}, 'turn_detection': None}}}
        await socket.send(json.dumps({'type': 'session.update', 'session': session}))
        # Never forward audio until the account accepts the expected session.
        async with asyncio.timeout(5):
            for _ in range(10):
                event = json.loads(await socket.recv())
                if event.get('type') == 'session.updated':
                    accepted = event.get('session', {})
                    audio = accepted.get('audio', {}).get('input', {})
                    if (accepted.get('type') != 'transcription'
                            or audio.get('transcription', {}).get('model') != MODEL
                            or audio.get('transcription', {}).get('languages') != ['en']
                            or audio.get('format') != session['audio']['input']['format']
                            or audio.get('turn_detection') is not None):
                        raise ValueError('The speech service returned an unsupported configuration.')
                    break
                if event.get('type') == 'error':
                    raise ValueError('The speech account could not start transcription. Use typing.')
            else:
                raise ValueError('Speech setup was not confirmed. Use typing.')
        yield socket


def audio_event(frame: bytes):
    return json.dumps({'type': 'input_audio_buffer.append', 'audio': base64.b64encode(frame).decode('ascii')})
