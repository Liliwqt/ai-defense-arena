"""Opt-in four-request Qwen diagnostic; no full-defense or latency-readiness claim."""
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
from unittest.mock import patch

import httpx

from backend.defense_session import DefenseTurn, PlannedMove, ResearchDefenseSession
from backend.evidence_response import lookup_format, read_result, EvidenceLookup
from backend.openrouter_questions import FRAMING_BYTES, RunQuestionClient, RunQuestionPolicy
from backend.openrouter_stream import stream
from backend.processing_policy import ProcessingWindowExpired
from backend.provider_allowance import ProviderAllowance
from backend.question_generator import QuestionDraft, GroundedQuestion, ResearchMove, TopicAssessmentDraft, _ground_question, build_project_source
from backend.turn_recovery import QuestionPlanRecovery
from tests.benchmark_transport import CampaignObserver, HTTPClient
from tests.reviewer_benchmark import local_ledger, failure_code
from tests.reviewer_cases import CASES

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT/'.scratch/defense-turn-responsiveness/reviews/08-impact-probe-fixtures.json'
PRIOR_PLAN = ROOT/'.scratch/defense-turn-responsiveness/reviews/08-provider-routing-plan.json'
MODEL = 'qwen/qwen3.8-flash'
ROUTES = {'alibaba-global': {'only': ['alibaba'], 'ignore': ['alibaba/us-east-1']},
          'alibaba-us-east': {'only': ['alibaba/us-east-1']}}


def saved_state(fixture, case):
    # Reconstructed fixtures use a stable synthetic identity, not a fresh live map.
    plan = replace(case.plan(), id='impact-probe:'+case.id)
    session = ResearchDefenseSession.create(plan, 5, 'research', 'proposal')
    session.coverage = deepcopy(fixture['coverage'])
    for item, index in zip(fixture['displayed'], fixture['answer_script_indices'], strict=True):
        line = item['citation_line']
        session.turns.append(DefenseTurn(item['panelist'], GroundedQuestion(item['question'],
            item['citation_file'], line, case.files[0].content.splitlines()[line-1], item['reaction']),
            answer=case.answers[index], topic_id=item['topic_id'], is_follow_up=item['is_follow_up']))
    plan = fixture['saved_plan']
    proposed = PlannedMove(plan['panelist'], plan['topic_id'], plan['is_follow_up'],
                           TopicAssessmentDraft.model_validate(plan['assessment']))
    session.validate_plan(proposed)
    return session, proposed


def _capture_body(fixture, case, policy):
    session, proposed = saved_state(fixture, case)
    scope = 'impact-probe-fixture:'+secrets.token_hex(12)
    ProviderAllowance(scope, 'synthetic-benchmark').establish(policy.ceiling_nano, asdict(policy))
    client = RunQuestionClient(scope, 'synthetic-benchmark', session, case.files, api_key='offline-fixture')
    history, context = session.answered_history(), session.context()
    recovery = QuestionPlanRecovery()
    recovery.seed('capture', client.plan_identity(history=history, context=context,
                  defense_type='research', research_stage='proposal'), proposed)
    client = RunQuestionClient(scope, 'synthetic-benchmark', session, case.files, api_key='offline-fixture',
                               recovery=recovery.claim('capture'))
    bodies = []
    def capture(request):
        body = json.loads(request.content)
        assert body['model'] == MODEL, 'No interpretation/planner/reviewer calls may be replayed.'
        bodies.append(body)
        normal = {'question': 'How will you evaluate the contribution within the stated setting?',
                  'lead_in': '', 'source_file': 1, 'evidence_line': 6}
        events = [{'choices': [{'index': 0, 'delta': {'content': json.dumps({'result': normal, 'lookup': None})},
                               'finish_reason': 'stop'}]}, {'usage': {'cost': 0}}]
        return httpx.Response(200, text=''.join('data: '+json.dumps(e)+'\n\n' for e in events)+'data: [DONE]\n\n')
    with patch('httpx.Client', side_effect=lambda **kw: HTTPClient(transport=httpx.MockTransport(capture), **kw)):
        client.research_move(case.files, history=history, context=context,
                             defense_type='research', research_stage='proposal')
    assert len(bodies) == 1
    return bodies[0]


def prepare_probes():
    fixtures = json.loads(FIXTURES.read_text())
    prior = json.loads(PRIOR_PLAN.read_text())
    result = []
    with TemporaryDirectory() as folder, local_ledger(Path(folder)):
        for index, fixture in enumerate(fixtures):
            case = next(c for c in CASES if c.id == fixture['case_id'])
            assert case.fingerprint == fixture['case_fingerprint'], 'Synthetic inputs changed.'
            original = next(r for r in prior['runs'] if r['case_id'] == case.id)
            policy = RunQuestionPolicy(**original['policy'])
            body = _capture_body(fixture, case, policy)
            bound = policy.stage_bound(len(json.dumps({'messages': body['messages'],
                'schema': body['response_format']}, ensure_ascii=False).encode())+FRAMING_BYTES, body['max_tokens'])
            for route, selectors in ROUTES.items():
                routed = deepcopy(body); routed['provider'].update(selectors)
                result.append({'case_id': case.id, 'case_fingerprint': case.fingerprint,
                    'route': route, 'body': routed, 'policy': policy, 'reserved_nano': bound,
                    'order': index})
    return result


def measurement_plan(probes):
    return {'evidence': 'plan-only', 'provider_gate': 'not-run', 'maximum_requests': len(probes),
        'ordinary_bound_nano': sum(p['reserved_nano'] for p in probes),
        'protocol': {'operation': 'reconstructed saved Impact question writer only',
            'reasoning': {'max_tokens': 2048}, 'output_tokens': 8192, 'window_ms': 45000,
            'retry': 'none: single-request diagnostic, not the full defense retry policy',
            'lookup': 'report lookup request without fetching or spending again',
            'models': 'unchanged; only Qwen is dispatched', 'routes': ROUTES,
            'inputs': 'same reconstructed synthetic history/evidence per case, not retained original request bytes',
            'scope': 'not a full turn or complete defense; no model promotion'},
        'fixture_sha256': hashlib.sha256(FIXTURES.read_bytes()).hexdigest(),
        'runs': [{k:v for k,v in p.items() if k not in {'body','policy'}} | {
            'request_sha256': hashlib.sha256(json.dumps(p['body'],sort_keys=True).encode()).hexdigest(),
            'policy': asdict(p['policy'])} for p in probes]}


def prepare_reasoning_probes():
    """Vary only the request's reasoning setting on the previously usable route."""
    result = []
    for probe in prepare_probes():
        if probe['route'] != 'alibaba-global':
            continue
        for condition, reasoning in (('reasoning-current', {'max_tokens': 2048}),
                                     ('reasoning-disabled', {'enabled': False})):
            candidate = deepcopy(probe)
            candidate['condition'] = condition
            candidate['body']['reasoning'] = reasoning
            candidate['request_reasoning'] = reasoning
            result.append(candidate)
    return result


def reasoning_measurement_plan(probes):
    plan = measurement_plan(probes)
    plan['protocol']['reasoning'] = 'request override only; captured base policy is unchanged'
    plan['protocol']['reasoning_conditions'] = {
        'reasoning-current': {'max_tokens': 2048}, 'reasoning-disabled': {'enabled': False}}
    plan['protocol']['routes'] = {'alibaba-global': ROUTES['alibaba-global']}
    return plan


def run_probe(probe, observer, key):
    case = next(c for c in CASES if c.id == probe['case_id'])
    started = monotonic(); deadline = started+45
    operation = secrets.token_hex(12)
    observer.context = {'condition': probe.get('condition', probe['route']), 'case_id': case.id,
        'case_fingerprint': case.fingerprint, 'operation_id': operation,
        'requested_route': ROUTES[probe['route']]}
    context = deepcopy(observer.context)
    completed = Queue(maxsize=1)
    client = observer.client(timeout=45)
    def current():
        if monotonic() >= deadline:
            raise ProcessingWindowExpired('Single-stage diagnostic window expired.')
    def dispatch():
        try:
            current()
            with client, stream(client, api_key=key, body=probe['body'],
                    schema=lookup_format(QuestionDraft), current=current, on_usage=lambda usage: None) as response:
                for _ in response: pass
                normal = read_result(response.get_final_response().output_parsed, QuestionDraft)
            if isinstance(normal, EvidenceLookup):
                value = {'outcome': 'lookup_requested'}
            else:
                _, lookup, _ = build_project_source(case.files)
                grounded = _ground_question(normal, lookup, set(lookup))
                fixture = next(f for f in json.loads(FIXTURES.read_text()) if f['case_id'] == case.id)
                session, selected = saved_state(fixture, case)
                session.apply_move(ResearchMove(selected.panelist, grounded, selected.topic_id,
                                               selected.is_follow_up, selected.assessment))
                value = {'outcome': 'succeeded', 'question': grounded.question,
                         'reaction': grounded.lead_in, 'citation_file': grounded.filename,
                         'citation_line': grounded.evidence_line}
        except Exception as error:
            value = {'outcome': 'failed', 'failure_class': type(error).__name__, 'failure_code': failure_code(error)}
        completed.put(value)
    Thread(target=dispatch, daemon=True, name='impact-route-probe').start()
    try:
        value = completed.get(timeout=max(0,deadline-monotonic()))
    except Empty:
        value = {'outcome': 'failed', 'failure_class': 'ProcessingWindowExpired',
                 'failure_code': 'processing_window_expired'}
    return {**context, 'duration_ms': round((monotonic()-started)*1000), **value}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--plan', action='store_true')
    mode.add_argument('--execute', action='store_true')
    parser.add_argument('--max-usd')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--reasoning-comparison', action='store_true',
                        help='current versus disabled reasoning on the same excluding-US-East route')
    args = parser.parse_args(argv)
    probes = prepare_reasoning_probes() if args.reasoning_comparison else prepare_probes()
    plan = reasoning_measurement_plan(probes) if args.reasoning_comparison else measurement_plan(probes)
    if not args.execute:
        print(json.dumps(plan,indent=2,sort_keys=True)); return 0
    try: cap = Decimal(args.max_usd or '0')
    except InvalidOperation: parser.error('A numeric separately approved campaign cap is required.')
    if not cap.is_finite() or not 0 < cap <= 1 or cap*10**9 != int(cap*10**9):
        parser.error('Use the separately approved cap, positive and at most USD1.')
    if not args.output or args.output.exists(): parser.error('Use a new output directory; never reset a ledger.')
    key = os.environ.get('OPENROUTER_API_KEY','').strip()
    if not key: parser.error('Configure the local key; never paste it in chat or arguments.')
    args.output.mkdir(parents=True)
    (args.output/'plan.json').write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n')
    outcomes = []
    with local_ledger(args.output):
        observer = CampaignObserver(secrets.token_hex(12),int(cap*10**9),probes[0]['policy'])
        # Reverse route order for the second case. No other model is dispatched.
        ordered = probes[:2]+list(reversed(probes[2:]))
        for probe in ordered:
            outcomes.append(run_probe(probe,observer,key))
            requests,active=observer.snapshot()
            (args.output/'results.json').write_text(json.dumps({'provider_gate':'unreviewed',
                'outcomes':outcomes,'requests':requests,'in_flight':active,
                'funding':observer.allowance.snapshot()},indent=2,sort_keys=True)+'\n')
            if outcomes[-1].get('failure_class') == 'AllowanceExhausted': break
    print('Probe complete. Review evidence; no app setting was changed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
