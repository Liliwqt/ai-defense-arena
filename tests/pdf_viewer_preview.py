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
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from backend import game_server as server, account_store, accounts
from backend.defense_session import ResearchDefenseSession
from backend.question_generator import GroundedCitation, GroundedQuestion, ResearchMove, RESEARCH_PANELISTS
from backend.research_plan import ResearchPlan, ResearchTopic
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
        uploads = [server.UploadedBytes('pilot-proposal.pdf', fixture_pdf([
            [('Campus pilot proposal',54,720)], [('Planned interviews with student volunteers',54,720)], [('Consent and anonymity',54,720)]])),
            server.UploadedBytes('repeated-evidence.pdf', fixture_pdf([[('Consent and anonymity',54,720),('Consent and anonymity',330,680)]]))]
        files, errors = read_research_files(uploads)
        assert not errors
        documents = server.app.state.documents.reserve(uploads)
        documents.stage(files, uploads)
        plan = ResearchPlan(tuple(ResearchTopic(f'topic-{i}', f'Pilot decision {i}', 'Explain this proposed decision.', role,
            (GroundedCitation(files[0].name, 2, files[0].content.splitlines()[1], files[0].locations[1], 'research_pdf'),))
            for i, role in enumerate(RESEARCH_PANELISTS, 1)))
        defense = ResearchDefenseSession.create(plan, 12, 'research', 'proposal')
        repeated = request.query_params.get('case') == 'repeated'
        cited = files[1] if repeated else files[0]
        line = 1 if repeated else 2
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
