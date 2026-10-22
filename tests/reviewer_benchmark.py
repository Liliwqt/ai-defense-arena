"""Opt-in reviewer comparisons; mocks never establish actual provider readiness."""
import argparse
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import secrets
from time import monotonic
from unittest.mock import patch
from pydantic_core import to_jsonable_python

from backend.defense_session import ResearchDefenseSession
from backend.processing_policy import ProcessingPolicy
from backend.provider_allowance import ProviderAllowance
from backend.room_operations import bind_operation, take_supplied_usage
from backend.streamlit_provider import ResearchProvider
from tests.benchmark_transport import CampaignObserver, USAGE
from tests.operation_timing_harness import summarize, compare, LOOKUP_FIELDS as LOOKUP
from tests.reviewer_cases import CASES, policies


def reconcile_records(records):
    """Join late request evidence without claiming incomplete usage is total cost."""
    result = deepcopy(records)
    for record in result:
        if record['event'] != 'total' or not record.get('operation_id'):
            continue
        stages = [r for r in result if r['event'] == 'stage' and r.get('operation_id') == record['operation_id']]
        for field in USAGE:
            record.pop(field, None)
        legacy_failure = record.get('capture_version') != 2 and record['outcome'] == 'failed'
        record['request_count'] = len(stages)
        record['request_count_is_lower_bound'] = legacy_failure
        record['in_flight_requests'] = sum(r['outcome'] == 'in_flight' for r in stages)
        if not legacy_failure:
            for field in USAGE:
                if stages and all(field in r for r in stages):
                    record[field] = sum(r[field] for r in stages)
    return result


def summarize_campaign(records):
    records = reconcile_records(records)
    conditions = {}
    for condition in sorted({r['condition'] for r in records}):
        selected = [r for r in records if r['condition'] == condition]
        completed = [r for r in selected if r.get('outcome') != 'in_flight']
        transitions = [r for r in selected if r['event'] == 'total' and r['kind'] == 'transition']
        ordinary = [r for r in transitions if r.get('phase') == 'answer']
        within_15 = sum(r['outcome'] == 'succeeded' and r['duration_ms'] <= 15000 for r in ordinary)
        conditions[condition] = {
            'transition_timing': summarize(transitions),
            'stages': summarize([r for r in completed if r['event'] == 'stage']),
            'in_flight_requests': sum(r['event'] == 'stage' and r['outcome'] == 'in_flight' for r in selected),
            'target': {'attempted': len(ordinary), 'within_15_seconds': within_15,
                'within_10_seconds': sum(r['outcome'] == 'succeeded' and r['duration_ms'] <= 10000 for r in ordinary),
                'fraction_within_15_seconds': within_15/len(ordinary) if ordinary else None},
            'by_model': {model: summarize([r for r in completed if r.get('model') == model])
                         for model in sorted({r['model'] for r in completed if r.get('model')})},
            'provider_identified_requests': sum(bool(r.get('provider')) for r in selected if r['event'] == 'stage'),
            'provider_unknown_requests': sum(not r.get('provider') for r in selected if r['event'] == 'stage'),
            'case_ids': sorted({r['case_id'] for r in transitions}),
            'automatic_retries': sum(r.get('automatic_retries', 0) for r in transitions),
            'retry_wait_ms': sum(r.get('retry_wait_ms', 0) for r in transitions),
            'broader_lookup': {field: {
                'sum': sum(r[field] for r in transitions if field in r) if any(field in r for r in transitions) else None,
                'known_records': sum(field in r for r in transitions),
                'unknown_records': sum(field not in r for r in transitions),
            } for field in LOOKUP},
        }
    comparisons = {name: compare([r for r in records if r['condition'] == 'baseline' and r['outcome'] != 'in_flight'],
                                [r for r in records if r['condition'] == name and r['outcome'] != 'in_flight'])
                   for name in conditions if name != 'baseline' and 'baseline' in conditions}
    return {'provider_gate': 'unreviewed', 'conditions': conditions, 'comparisons': comparisons}


def measurement_plan():
    configured = policies()
    rows = []
    for case in CASES:
        for condition, policy in configured.items():
            captured = policy.snapshotted(case.files, 5)
            rows.append({'case_id': case.id, 'case_fingerprint': case.fingerprint,
                'condition': condition, 'field': case.field, 'approach': case.approach,
                'language': case.language, 'source_bytes': sum(len(f.content.encode()) for f in case.files),
                'defense_type': 'mixed' if case.mixed else 'research',
                'policy': asdict(captured), 'ordinary_bound_nano': captured.question_bound(case.files, 5),
                'admission_problem': captured.viability_problem(case.files, 5)})
    return {'evidence': 'plan-only', 'provider_gate': 'not-run', 'runs': rows,
        'conditions': list(configured), 'cases': len(CASES),
        'protocol': {'question_budget': 5, 'answered_turns': 4, 'maximum_same_question_replies': 1,
            'preparation': 'identical locally validated synthetic maps; no provider mapping call',
            'coaching': 'protected funds retained; no provider coaching call',
            'processing': 'same current 45-second policy in all conditions',
            'order': 'conditions rotated per case; one repeat is exploratory, not a power claim',
            'baseline': 'previous separate/full OpenRouter policy, not GPT Luna',
            'quality': 'manual review required for every role and condition',
            'notes': 'identical sources/answer scripts; adaptive dialogue paths may differ'},
        'ordinary_bound_nano': sum(row['ordinary_bound_nano'] for row in rows)}


def run_case(case, condition, policy, observer, *, evidence, on_measure=None):
    """Exercise actual typed/provider contracts in isolated benchmark scopes."""
    session = ResearchDefenseSession.create(case.plan(), 5, 'mixed' if case.mixed else 'research', 'proposal')
    identity = secrets.token_hex(12)
    scope = 'benchmark-run:'+identity
    captured = policy.snapshotted(case.files, 5)
    problem = captured.viability_problem(case.files, 5)
    if problem:
        raise ValueError('Synthetic case exceeds the unchanged run ceiling; do not increase it for this benchmark.')
    ProviderAllowance(scope, 'synthetic-benchmark').establish(captured.ceiling_nano, asdict(captured))
    practice = ResearchProvider('synthetic-benchmark', 'benchmark-preparation:'+identity,
                                run_scope=scope, session=session)
    flow = practice.flow(session, case.files)
    # Keep the same safety window on the old pipeline for a fair, bounded
    # comparison. This does not claim to replay its old unbounded waiting UI.
    flow.processing = ProcessingPolicy.standard()
    policy_digest = hashlib.sha256(json.dumps(asdict(captured), sort_keys=True).encode()).hexdigest()
    metadata = {'case_id': case.id, 'case_fingerprint': case.fingerprint,
        'capture_version': 2,
        'condition': condition, 'run_id': identity, 'evidence': evidence,
        'policy_fingerprint': policy_digest, 'source_bytes': sum(len(f.content.encode()) for f in case.files)}
    records, quality = [], []
    from backend.question_generator import RESEARCH_PANELISTS

    def measure(phase, action, answer_index=None):
        operation = secrets.token_hex(16)
        outgoing = session.turns[-1].panelist if session.turns else None
        observer.context = {**metadata, 'operation_id': operation, 'outgoing_role': outgoing}
        bind_operation(operation)
        started = monotonic()
        result = None
        failure = None
        statuses = []
        interpreted = []
        validated_plans = []
        from backend import question_generator
        interpret = question_generator.interpret_submission
        seed = practice.question_recovery.seed
        def observe_validated_plan(namespace, identity, plan):
            seed(namespace, identity, plan)
            validated_plans.append(to_jsonable_python(plan))
        def observe_interpretation(*args, **kwargs):
            decision = interpret(*args, **kwargs)
            # This is a parsed domain result, not raw model JSON. A writer may
            # fail after the server validates and saves its proposed next plan.
            interpreted.append(to_jsonable_python(decision))
            return decision
        try:
            with patch.object(question_generator, 'interpret_submission', side_effect=observe_interpretation), \
                    patch.object(practice.question_recovery, 'seed', side_effect=observe_validated_plan):
                result = action(lambda text: statuses.append((monotonic(),text)))
        except Exception as error:
            failure = type(error).__name__
        elapsed = round((monotonic()-started)*1000)
        supplied = take_supplied_usage(operation)
        stages, _ = observer.snapshot()
        stages = [r for r in stages if r.get('operation_id') == operation]
        record = {**metadata, 'event': 'total', 'kind': 'transition', 'operation_id': operation,
            'phase': 'completion' if session.completed else phase, 'duration_ms': elapsed,
            'outgoing_role': outgoing, 'request_count': len(stages),
            'automatic_retries': sum(text.startswith('Trying again') for _,text in statuses),
            'retry_wait_ms': round(sum((statuses[i+1][0] if i+1<len(statuses) else monotonic())-stamp
                for i,(stamp,text) in enumerate(statuses) if text.startswith('Waiting to retry'))*1000),
            'outcome': 'failed' if failure else 'same_question' if result in {'clarified', 'probed'} else 'succeeded',
            **({'failure_class': failure} if failure else {})}
        for field in USAGE:
            if stages and all(field in r for r in stages):
                record[field] = sum(r[field] for r in stages)
        record.update({key: supplied[key] for key in LOOKUP if key in supplied})
        records.append(record)
        # A separate synthetic-only review artifact contains validated displayed
        # dialogue, never raw provider JSON/reasoning or submitted answer text.
        quality.append({**metadata, 'operation_id': operation, 'phase': record['phase'],
            'outgoing_role': outgoing, 'answer_script_index': answer_index,
            'decision': result, 'failure_class': failure,
            'interpretation_results': deepcopy(interpreted),
            'validated_next_plans': deepcopy(validated_plans),
            'coverage': deepcopy(session.coverage),
            'displayed': [{'panelist': turn.panelist, 'question': turn.question.question,
                'reaction': turn.question.lead_in,
                'topic_id': turn.topic_id, 'is_follow_up': turn.is_follow_up,
                'citation_file': turn.question.filename, 'citation_line': turn.question.evidence_line,
                'clarifications': [c.reply for c in turn.clarifications],
                'probe': turn.probe.request if turn.probe else None} for turn in session.turns],
            'manual_review': {'grounding': None, 'scrutiny': None, 'brevity': None,
                'language': None, 'combined_decision': None, 'notes': None}})
        if on_measure:
            on_measure(records, quality)
        return failure is None

    with patch('httpx.Client', side_effect=observer.client):
        if measure('opening', lambda notify: flow.advance(notify=notify)):
            for _ in range(4):
                if session.completed or not session.awaiting_answer:
                    break
                turn = len(session.turns)
                index = RESEARCH_PANELISTS.index(session.turns[-1].panelist)
                if not measure('answer', lambda notify: flow.submit(case.answers[index],notify=notify), index):
                    break
                if len(session.turns) == turn and session.awaiting_answer:
                    if not measure('reply', lambda notify: flow.submit(case.answers[index],notify=notify), index):
                        break
                if len(session.turns) == turn and not session.completed:
                    break
    practice.cancel()
    return records, quality


def run_campaign(observer, *, evidence, on_case=None):
    records, quality = [], []
    configured = policies()
    conditions = list(configured)
    for index, case in enumerate(CASES):
        order = conditions[index % len(conditions):] + conditions[:index % len(conditions)]
        for condition in order:
            rows, review = run_case(case, condition, configured[condition], observer, evidence=evidence,
                on_measure=(lambda new, review: on_case(records+new, quality+review)) if on_case else None)
            records.extend(rows); quality.extend(review)
            if on_case:
                on_case(records, quality)
            if any(r.get('failure_class') == 'AllowanceExhausted' for r in rows):
                stages, active = observer.snapshot()
                return records+stages, quality, active
    stages, active = observer.snapshot()
    return records+stages, quality, active


@contextmanager
def local_ledger(folder):
    with patch.dict(os.environ, {'DATABASE_URL': '', 'PAYMONGO_TEST_DB_PATH': str(folder/'ledger.sqlite3')}):
        yield


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--plan', action='store_true')
    mode.add_argument('--execute', action='store_true', help='explicitly authorize the prepared synthetic provider requests')
    parser.add_argument('--max-usd', help='approved hard campaign spending ceiling')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    plan = measurement_plan()
    if not args.execute:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0
    if not args.output or not args.max_usd:
        parser.error('--execute needs an approved --max-usd and a new --output directory')
    try:
        cap = Decimal(args.max_usd)
    except InvalidOperation:
        parser.error('use a numeric approved spending ceiling')
    if not cap.is_finite() or not Decimal('0') < cap <= 100 or cap*1_000_000_000 != int(cap*1_000_000_000):
        parser.error('use a positive approved ceiling with at most nine decimal places, no more than USD100')
    if not os.environ.get('OPENROUTER_API_KEY', '').strip():
        parser.error('configure OPENROUTER_API_KEY locally; never put it in arguments or artifacts')
    if args.output.exists():
        parser.error('use a new output directory; existing evidence and spending holds are never overwritten')
    args.output.mkdir(parents=True)
    (args.output/'plan.json').write_text(json.dumps(plan, indent=2, sort_keys=True)+'\n')
    def write(records, quality):
        stages, active = observer.snapshot()
        reconciled = reconcile_records(records+stages)
        (args.output/'measurements.jsonl').write_text(''.join(json.dumps(r, sort_keys=True)+'\n' for r in reconciled))
        (args.output/'quality-review.json').write_text(json.dumps(quality, indent=2, sort_keys=True)+'\n')
        report = summarize_campaign(reconciled)
        report.update(evidence='actual-provider', in_flight_requests=active,
                      funding={k: int(v) for k,v in observer.allowance.snapshot().items()})
        observed = {(r['case_id'], r['condition']) for r in records}
        report['not_run'] = [{'case_id': row['case_id'], 'condition': row['condition']}
                             for row in plan['runs'] if (row['case_id'],row['condition']) not in observed]
        (args.output/'report.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    with local_ledger(args.output):
        observer = CampaignObserver(secrets.token_hex(16), int(cap*1_000_000_000), policies()['current'])
        records, quality, active = run_campaign(observer, evidence='actual-provider', on_case=write)
        # run_campaign returns stage rows too; write takes transition rows only.
        write([r for r in records if r['event'] == 'total'], quality)
    print('Evidence written. Provider gate remains unreviewed; no production setting was changed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
