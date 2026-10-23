"""Opt-in two-request Critical diagnostic; no full-defense or quality claim."""
import argparse
from copy import deepcopy
from dataclasses import asdict, replace
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
from queue import Queue, Empty
import secrets
from tempfile import TemporaryDirectory
from threading import Thread
from time import monotonic
from types import SimpleNamespace
from typing import get_args
from unittest.mock import patch

import httpx

from backend.defense_session import DefenseTurn, PlannedMove, ResearchDefenseSession
from backend.evidence_response import EvidenceLookup, read_result
from backend.openrouter_questions import COMBINED_PLANNING_GUIDANCE, FRAMING_BYTES, RunQuestionClient, RunQuestionPolicy
from backend.openrouter_stream import stream
from backend.processing_policy import ProcessingWindowExpired
from backend.provider_allowance import ProviderAllowance
from backend.question_generator import (
    CombinedSubmissionDraft, CRITICAL_JUDGE, GroundedQuestion, RESEARCH_PANELISTS,
    build_project_source, ground_source_reference, interpret_submission,
)
from tests.benchmark_transport import CampaignObserver, HTTPClient
from tests.reviewer_benchmark import failure_code, local_ledger
from tests.reviewer_cases import CASES

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / '.scratch/defense-turn-responsiveness/reviews/08-critical-replay-fixture.json'
PLAN = ROOT / '.scratch/defense-turn-responsiveness/reviews/08-complete-candidate-plan.json'


def replay_inputs():
    fixture = json.loads(FIXTURE.read_text())
    case = next(c for c in CASES if c.id == fixture['case_id'])
    assert case.fingerprint == fixture['case_fingerprint'], 'Synthetic source/scripts changed.'
    policy = RunQuestionPolicy(**next(r['policy'] for r in json.loads(PLAN.read_text())['runs']
                                     if r['case_id'] == case.id))
    session = ResearchDefenseSession.create(replace(case.plan(), id='critical-probe:'+case.id),
                                           8, 'research', 'proposal')
    session.coverage = deepcopy(fixture['coverage'])
    _, lookup, _ = build_project_source(case.files)
    for index, item in enumerate(fixture['displayed']):
        assert not item['clarifications'] and item['probe'] is None, 'Unsupported replay exchange.'
        assert item['citation_file'] == case.files[0].name and item['topic_id'] in session.coverage
        line = item['citation_line']
        citation = ground_source_reference(1, line, lookup, {1})
        question = GroundedQuestion(item['question'], lead_in=item['reaction'], **asdict(citation))
        session.turns.append(DefenseTurn(item['panelist'], question,
            answer=case.answers[RESEARCH_PANELISTS.index(item['panelist'])]
                if index < len(fixture['displayed'])-1 else None,
            topic_id=item['topic_id'], is_follow_up=item['is_follow_up']))
    assert len(session.turns) == 7 and session.turns[-1].panelist == CRITICAL_JUDGE and session.awaiting_answer
    candidate = deepcopy(session)
    candidate.turns[-1].answer = case.answers[3]
    context = candidate.context()
    context['current_topic'] = candidate.turns[-1].topic_id
    return case, policy, session, candidate, context


def interpret(client):
    case, _, session, candidate, context = replay_inputs()
    decision = interpret_submission(case.files, None, panelist=CRITICAL_JUDGE,
        question=session.turns[-1].question, submission=case.answers[3],
        history=session.answered_history(), defense_type='research', research_stage='proposal',
        research_context=context, planning_context=context, planning_guidance=COMBINED_PLANNING_GUIDANCE,
        text_format=CombinedSubmissionDraft, client=client)
    if decision.action == 'answer':
        plan = decision.plan
        candidate.validate_plan(PlannedMove(plan.panelist, plan.topic_id, plan.is_follow_up, plan.assessment))
    return decision


def prepare_probe():
    case, policy, session, _, _ = replay_inputs()
    bodies = []
    schemas = []
    def capture_schema(*args, **kwargs):
        schemas.append(kwargs['schema'])
        return stream(*args, **kwargs)
    def capture(request):
        body = json.loads(request.content)
        assert body['model'] == policy.reviewer_models[CRITICAL_JUDGE]
        assert body['response_format']['json_schema']['name'] == 'CombinedSubmissionDraft'
        bodies.append(body)
        value = {'result': {'action': 'clarify', 'clarification': 'Explain which comparison assumption you mean.',
                           'probe': None}, 'lookup': None}
        return httpx.Response(200, text='data: '+json.dumps({'choices': [{'index': 0,
            'delta': {'content': json.dumps(value)}, 'finish_reason': 'stop'}]})+'\n\ndata: [DONE]\n\n')
    with TemporaryDirectory() as folder, local_ledger(Path(folder)):
        scope = 'critical-probe-capture:'+secrets.token_hex(12)
        ProviderAllowance(scope, 'synthetic-benchmark').establish(policy.ceiling_nano, asdict(policy))
        client = RunQuestionClient(scope, 'synthetic-benchmark', session, case.files, api_key='offline-fixture')
        with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(capture), **kw)), \
                patch('backend.openrouter_questions.open_stream', side_effect=capture_schema):
            interpret(client.interaction(CRITICAL_JUDGE, combined=True))
    assert len(bodies) == len(schemas) == 1
    body = bodies[0]
    bound = policy.stage_bound(len(json.dumps({'messages': body['messages'],
        'schema': body['response_format']}, ensure_ascii=False).encode())+FRAMING_BYTES, body['max_tokens'])
    result_schema, = (schema for schema in get_args(schemas[0].model_fields['result'].annotation)
                      if schema is not type(None))
    return {'case_id': case.id, 'case_fingerprint': case.fingerprint,
            'body': body, 'schema': schemas[0], 'result_schema': result_schema,
            'policy': policy, 'reserved_nano': bound}


def measurement_plan(probe):
    return {'evidence': 'plan-only', 'provider_gate': 'not-run', 'maximum_requests': 2,
        'ordinary_bound_nano': 2*probe['reserved_nano'], 'case_id': probe['case_id'],
        'case_fingerprint': probe['case_fingerprint'], 'model': probe['body']['model'],
        'reasoning': probe['body']['reasoning'], 'max_tokens': probe['body']['max_tokens'],
        'provider': probe['body']['provider'], 'policy': asdict(probe['policy']),
        'request_sha256': hashlib.sha256(json.dumps(probe['body'],sort_keys=True).encode()).hexdigest(),
        'fixture_sha256': hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        'protocol': {'operation': 'two identical reconstructed Critical combined-review requests',
            'window_ms': 45000, 'retry': 'none', 'lookup': 'report without expansion or another request',
            'validation': 'unchanged submission and prospective-plan validators, no state publication',
            'earlier_stages': 'reconstructed synthetic history only; no mapping/planning/question/coaching request',
            'limitation': 'new stable synthetic map ID; not original retained wire bytes or proof of historical cause'}}


def run_probe(probe, observer, key, attempt):
    started = monotonic(); deadline = started+45
    operation = secrets.token_hex(12)
    context = {'condition': 'critical-replay', 'case_id': probe['case_id'],
               'case_fingerprint': probe['case_fingerprint'], 'operation_id': operation, 'attempt': attempt}
    observer.context = context
    client = observer.client(timeout=45)
    completed = Queue(maxsize=1)
    def current():
        if monotonic() >= deadline:
            raise ProcessingWindowExpired('Single-stage diagnostic window expired.')
    def dispatch():
        try:
            current()
            with client, stream(client, api_key=key, body=probe['body'], schema=probe['schema'],
                    current=current, on_usage=lambda usage: None) as response:
                for _ in response: pass
                normal = read_result(response.get_final_response().output_parsed, probe['result_schema'])
            current()
            if isinstance(normal, EvidenceLookup):
                value = {'outcome': 'lookup_requested'}
            else:
                offline = SimpleNamespace(responses=SimpleNamespace(parse=lambda **kw:
                    SimpleNamespace(output_parsed=normal)))
                decision = interpret(offline)
                current()
                value = {'outcome': 'succeeded', 'validated_action': decision.action}
        except Exception as error:
            value = {'outcome': 'failed', 'failure_class': type(error).__name__, 'failure_code': failure_code(error)}
        completed.put(value)
    Thread(target=dispatch, daemon=True, name='critical-review-probe').start()
    try:
        value = completed.get(timeout=max(0,deadline-monotonic()))
    except Empty:
        value = {'outcome': 'failed', 'failure_class': 'ProcessingWindowExpired', 'failure_code': 'processing_window_expired'}
    return {**context, 'duration_ms': round((monotonic()-started)*1000), **value}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--plan', action='store_true')
    mode.add_argument('--execute', action='store_true')
    parser.add_argument('--max-usd')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    probe = prepare_probe(); plan = measurement_plan(probe)
    if not args.execute:
        print(json.dumps(plan, indent=2, sort_keys=True)); return 0
    try: cap = Decimal(args.max_usd or '0')
    except InvalidOperation: parser.error('A numeric separately approved cap is required.')
    if not cap.is_finite() or not 0 < cap <= 1 or cap*10**9 != int(cap*10**9):
        parser.error('Use a separately approved positive cap of at most USD1.')
    if not args.output or args.output.exists(): parser.error('Use a new directory; never reset a campaign ledger.')
    # A timed-out daemon may still reconcile a receipt after local_ledger exits.
    # Its restored environment must resolve to this same isolated ledger.
    ledger = str((args.output/'ledger.sqlite3').resolve())
    if os.environ.get('DATABASE_URL') != '' or os.environ.get('PAYMONGO_TEST_DB_PATH') != ledger:
        parser.error('Use the prepared isolated launcher; database settings must already target this campaign ledger.')
    key = os.environ.get('OPENROUTER_API_KEY','').strip()
    if not key: parser.error('Configure the local key; never send it in chat or arguments.')
    args.output.mkdir(parents=True)
    (args.output/'plan.json').write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n')
    outcomes = []
    with local_ledger(args.output):
        observer = CampaignObserver(secrets.token_hex(12), int(cap*10**9), probe['policy'])
        for attempt in range(2):
            outcomes.append(run_probe(probe,observer,key,attempt))
            requests, active = observer.snapshot()
            (args.output/'results.json').write_text(json.dumps({'provider_gate':'unreviewed',
                'outcomes':outcomes, 'requests':requests, 'in_flight':active,
                'funding':observer.allowance.snapshot()},indent=2,sort_keys=True)+'\n')
            if outcomes[-1].get('failure_class') == 'AllowanceExhausted': break
    print('Diagnostic complete. Review evidence; no runtime setting was changed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
