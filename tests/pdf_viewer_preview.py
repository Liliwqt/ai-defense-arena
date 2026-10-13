"""Loopback-only synthetic room with real PDFs; no external provider requests.

Run from the repository root: .venv/bin/python -m tests.pdf_viewer_preview
This wrapper is never mounted by the production application.
"""

import asyncio
from contextlib import asynccontextmanager
import json
import os
import secrets
from io import BytesIO
from tempfile import TemporaryDirectory
from textwrap import wrap
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from backend import game_server as server, account_store, accounts
from backend.defense_session import ResearchDefenseSession
from backend.question_generator import GroundedCitation, GroundedQuestion, ResearchMove, RESEARCH_PANELISTS
from backend.research_plan import ResearchPlan, ResearchTopic, ResearchProfile
from backend.research_files import read_research_files
from backend.rooms.coordinator import RoomCoordinator, RoomWorkflows

def fixture_pdf(pages):
    """Readable letter-size fixture; each page contains positioned text runs."""
    writer = PdfWriter()
    for runs in pages:
        page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
        stream = DecodedStreamObject()
        stream.set_data('\n'.join(f'BT /F1 12 Tf {x} {y} Td ({text}) Tj ET' for text,x,y in runs).encode())
        page[NameObject('/Contents')] = writer._add_object(stream)
    result = BytesIO(); writer.write(result)
    return result.getvalue()


def proposal_pages():
    """Full synthetic reading pages, with a unique citation among other text."""
    sections = [
        ('Campus pilot proposal', [
            'Synthetic proposal for local viewer review. This is a demonstration document, not an actual completed study.',
            'Background and purpose',
            'Students may find it difficult to judge when a campus service queue is likely to be busy. This proposal explores whether a simple queue information tool could help students plan a visit without requiring them to share personal schedules.',
            'The proposed tool would show an approximate queue status and explain when that status was last updated. The pilot would examine whether students understand the information, how they use it, and which details they find confusing.',
            'Research objectives',
            'The team plans to describe current waiting experiences, identify useful information, and evaluate a small prototype. The study would distinguish a participant preference from a measured change in waiting time.',
            'Scope and boundaries',
            'The first pilot would focus on one campus service. It would not automatically represent other offices, campuses, or students who cannot attend the planned sessions. Recruitment and access limitations would be reported alongside any findings.',
            'No results have been collected. The proposed activities, ethical safeguards, and evaluation approach remain subject to review before recruitment begins.',
            'Reading note: use Previous and Next to browse each complete page. The highlighted passage for the current defense question appears on the methodology page.',
        ]),
        ('Methodology and recruitment', [
            'Synthetic proposal for local viewer review. All activities described here are planned.',
            'Study design',
            'The team proposes a small exploratory pilot combining interviews and prototype tasks. Interviews would explore current queue experiences, while tasks would examine whether participants can interpret the proposed status display.',
            'Planned interviews with student volunteers',
            'Recruitment would be announced through available campus channels. Interested students would receive an explanation of the study before choosing whether to join. Participation would not affect access to the campus service.',
            'The team still needs to explain how recruitment could include students with different schedules and levels of interest in the tool. Recruiting only supporters might limit the range of experiences described in the interviews.',
            'Prototype tasks',
            'Participants would read a sample queue status, identify its update time, and explain what they would do next. The team would record task completion and points of confusion without assuming that a correct task response proves shorter real-world waits.',
            'Analysis and feasibility',
            'Interview notes would be grouped into recurring themes. Task observations would be summarized descriptively. The team would report contradictory comments rather than selecting only feedback that supports the proposed design.',
            'Before starting, the team would confirm permission to use the study setting, available session times, and a practical recruitment target. Changes to the plan would be documented before interpreting the pilot evidence.',
            'Limitations include voluntary recruitment, a single study setting, and the difference between a demonstration task and everyday use. These limitations would guide how cautiously the team describes the findings.',
        ]),
        ('Ethics and expected contribution', [
            'Synthetic proposal for local viewer review. This page presents proposed safeguards, not evidence that a study has already been approved.',
            'Consent and anonymity',
            'Participants would receive a plain-language explanation of the purpose, activities, expected duration, and right to stop. The team would obtain any required institutional approval before contacting volunteers.',
            'Interview notes would use participant codes rather than names. Contact information needed for scheduling would be kept separately and accessed only by authorized team members.',
            'The proposed prototype would avoid collecting student schedules or account credentials. If the study design changes to require more sensitive information, the team would revisit consent and data handling before collection.',
            'Expected contribution',
            'The pilot could identify which queue information students understand and which design assumptions require revision. These are expected contributions, not reported results or a promise that the tool will reduce waiting times.',
            'The team would consider both useful feedback and situations where the information does not help. Any recommendation to extend the tool would depend on the evidence collected and the limits of the pilot.',
            'Reporting and next steps',
            'The final report would connect conclusions to observations, disclose recruitment limitations, and separate participant suggestions from verified outcomes. Open questions would be recorded for future study.',
            'This demonstration paper is intentionally long enough to review page scrolling, zoom, page navigation, and citation placement without uploading a private research document.',
        ]),
    ]
    pages = []
    for number, (title, paragraphs) in enumerate(sections, 1):
        runs = [(title, 54, 738)]
        y = 706
        for paragraph in paragraphs:
            for line in wrap(paragraph, width=72):
                runs.append((line, 54, y))
                y -= 16
            y -= 10
        runs.append((f'Synthetic viewer fixture - page {number}', 54, 42))
        pages.append(runs)
    return pages


def preview_app():
    @asynccontextmanager
    async def lifespan(_):
        async with server.lifespan(server.app):
            yield
    app = FastAPI(lifespan=lifespan)

    @app.get('/__fixture/login')
    async def login(request: Request):
        if request.client.host != '127.0.0.1':
            raise HTTPException(403, 'Local fixture only.')
        token, _ = account_store.create_google_session('pdf-preview', 'fixture@example.test', 'Alex — fixture')
        account = account_store.session_account(token)
        account_store.redeem_voucher(account['id'], os.environ['FREE_ACCESS_VOUCHER'])
        uploads = [server.UploadedBytes('pilot-proposal.pdf', fixture_pdf(proposal_pages())),
            server.UploadedBytes('repeated-evidence.pdf', fixture_pdf([[('Consent and anonymity',54,720),('Consent and anonymity',330,680)]]))]
        files, errors = read_research_files(uploads)
        assert not errors
        citation_line = files[0].content.splitlines().index('Planned interviews with student volunteers') + 1
        documents = server.app.state.documents.reserve(uploads)
        documents.stage(files, uploads)
        topics = tuple(ResearchTopic(f'topic-{i}', f'Pilot decision {i}', 'Explain this proposed decision.', role,
            (GroundedCitation(files[0].name, citation_line, files[0].content.splitlines()[citation_line-1], files[0].locations[citation_line-1], 'research_pdf'),))
            for i, role in enumerate(RESEARCH_PANELISTS, 1))
        profile = ResearchProfile(("Human-computer interaction", "Education"),
            ("qualitative", "computational/design"), "One campus service",
            "The proposal combines volunteer interviews and exploratory prototype tasks.",
            topics[0].references, ("Recruitment coverage remains to be explained.",))
        plan = ResearchPlan(topics, profile=profile)
        defense = ResearchDefenseSession.create(plan, 12, 'research', 'proposal')
        repeated = request.query_params.get('case') == 'repeated'
        cited = files[1] if repeated else files[0]
        line = 1 if repeated else citation_line
        question_text = 'How will you recruit volunteers without selecting only students who already agree with the proposed pilot?'
        if request.query_params.get('case') == 'long':
            question_text += ' Explain how access to different departments, class schedules and voluntary participation affects your recruitment choices. Identify the proposed comparison and the limitation you would disclose before interpreting the pilot findings.'
        question = GroundedQuestion(question_text,
            cited.name, line, cited.content.splitlines()[line-1], evidence_location=cited.locations[line-1], evidence_kind='research_pdf')
        defense.apply_move(ResearchMove(RESEARCH_PANELISTS[0], question, 'topic-1', False, None))
        code = server._room_code(); player_token = server._new_token()
        room = server.Room(code, files, {player_token: server.Player(player_token, 'Alex — fixture', 0, True)},
            'research', 'proposal', defense=defense, documents=documents, owner_account_id=account['id'],
            research_plan=plan, research_plan_approved=True, research_planning_status='ready', research_budget_preview=12)
        room.phase = 'question'; room.selected_seat = 0
        # Fixed synthetic clock makes the visual fixture stable; protocol tests
        # separately exercise actual server-owned deadline progression.
        room.answer_deadline_ms = 1_120_000
        async def blocked(_):
            await asyncio.Event().wait()
        if request.query_params.get('case') == 'mapping':
            # Deliberately paced synthetic events for visual review, not an AI
            # request or evidence of actual provider timing/quality.
            from backend.research_plan import ResearchPlanProgress
            async def preview_map(request):
                await request.on_progress(ResearchPlanProgress('mapping'))
                for count in range(1, len(plan.topics) + 1):
                    await asyncio.sleep(1.5)
                    if not await request.on_progress(ResearchPlanProgress('mapping', plan.topics[:count])):
                        raise RuntimeError('Preview mapping cancelled')
                await request.on_progress(ResearchPlanProgress('validating', plan.topics))
                await asyncio.sleep(1)
                return plan
            room.phase = 'lobby'
            room.defense = None
            room.selected_seat = None
            room.answer_deadline_ms = None
            room.research_plan = None
            room.research_plan_approved = False
            room.research_planning_status = 'none'
            room.research_budget_preview = None
            RoomCoordinator(room, RoomWorkflows(plan_request=preview_map))
        else:
            RoomCoordinator(room, RoomWorkflows(now=lambda: 1_000_000, sleep=blocked))
        server.rooms[code] = room
        response = HTMLResponse('<script>localStorage.setItem("defense_room_code", '+json.dumps(code)+');'
            'localStorage.setItem("defense_player_token", '+json.dumps(player_token)+');location.replace("/");</script>')
        response.set_cookie(accounts.ACCOUNT_COOKIE, token, httponly=True, samesite='lax')
        return response

    app.mount('/', server.app)
    return app


if __name__ == '__main__':
    import uvicorn
    with TemporaryDirectory(prefix='pdf-viewer-preview-') as folder:
        for name in ('OPENAI_API_KEY', 'DATABASE_URL', 'PAYMONGO_SECRET_KEY', 'PAYMONGO_LIVE_SECRET_KEY'):
            os.environ.pop(name, None)
        os.environ.update({'PAYMENTS_MODE': 'test', 'PAYMONGO_TEST_DB_PATH': folder+'/accounts.sqlite3',
            'ROOM_DOCUMENT_DIR': folder+'/documents', 'GOOGLE_CLIENT_ID': 'offline-client',
            'GOOGLE_CLIENT_SECRET': 'offline-secret', 'AUTH_SESSION_SECRET': secrets.token_hex(32),
            'AUTH_PUBLIC_BASE_URL': 'http://127.0.0.1:8842', 'FREE_ACCESS_VOUCHER': 'offline-pdf-fixture'})
        uvicorn.run(preview_app(), host='127.0.0.1', port=8842)
