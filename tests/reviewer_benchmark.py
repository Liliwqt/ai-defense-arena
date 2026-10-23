"""Opt-in reviewer comparisons; mocks never establish actual provider readiness."""
import argparse
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict, replace
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
from backend.openrouter_questions import EVIDENCE_FULL
from backend.processing_policy import ProcessingPolicy
from backend.provider_allowance import ProviderAllowance
from backend.room_operations import bind_operation, take_supplied_usage
from backend.streamlit_provider import ResearchProvider
from tests.benchmark_transport import CampaignObserver, USAGE
from tests.operation_timing_harness import summarize, compare, LOOKUP_FIELDS as LOOKUP
from tests.reviewer_cases import CASES, policies


def failure_code(error):
    from backend.response_diagnostics import safe_response_code
    code = safe_response_code(error)
    if code is not None:
        return code
    from backend.processing_policy import ProcessingWindowExpired
    from backend.openrouter_stream import ProviderStatusError
    from backend.question_generator import InvalidQuestionResponse
    if isinstance(error, ProcessingWindowExpired):
        return 'processing_window_expired'
    if isinstance(error, ProviderStatusError):
        return 'http_'+str(error.status_code)
    if isinstance(error, InvalidQuestionResponse):
        return 'invalid_result'
    return 'unclassified'


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
            **({'coaching_timing': summarize([r for r in selected if r['event'] == 'total' and
                                             r['kind'] == 'coaching'])}
               if any(r['kind'] == 'coaching' for r in selected) else {}),
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


def provider_comparison():
    """Only the DeepSeek host changes; every captured task policy stays identical."""
    current = policies()['current']
    model = 'deepseek/deepseek-v4.1-flash-1017'
    if current.provider_only or model not in current.reviewer_models.values():
        raise ValueError('Provider comparison requires the reviewed unpinned Standard DeepSeek policy.')
    configured = {'provider-auto': current, 'provider-deepinfra': current}
    return configured, {'provider-auto': {}, 'provider-deepinfra': {model: 'deepinfra'}}


def complete_candidate():
    """The measured candidate, isolated from app defaults and existing runs."""
    current = policies()['current']
    if (current.provider_only or current.reviewer_models['Methodology Reviewer'] !=
            'deepseek/deepseek-v4.1-flash-1017' or current.reviewer_models['Impact Reviewer'] !=
            'qwen/qwen3.8-flash'):
        raise ValueError('Re-review the candidate after changing the captured model bundle.')
    candidate = replace(current, reviewer_reasoning={**current.reviewer_reasoning,
        'Impact Reviewer': {'enabled': False}})
    return {'complete-candidate': candidate}, {'complete-candidate': {
        current.reviewer_models['Methodology Reviewer']: 'deepinfra',
        current.reviewer_models['Impact Reviewer']: {'only': ['alibaba'], 'ignore': ['alibaba/us-east-1']}}}


def measurement_plan(cases=CASES, configured=None, *, provider_routes=None, complete=False):
    configured = policies() if configured is None else configured
    budget = 8 if complete else 5
    rows = []
    for case in cases:
        for condition, policy in configured.items():
            captured = policy.snapshotted(case.files, budget)
            rows.append({'case_id': case.id, 'case_fingerprint': case.fingerprint,
                'condition': condition, 'field': case.field, 'approach': case.approach,
                'language': case.language, 'source_bytes': sum(len(f.content.encode()) for f in case.files),
                'defense_type': 'mixed' if case.mixed else 'research',
                'policy': asdict(captured),
                **({'coaching_bound_nano': captured.coaching_bound(case.files, budget)} if complete else {}),
                'ordinary_bound_nano': captured.question_bound(case.files, budget) +
                    (captured.coaching_bound(case.files, budget) if complete else 0),
                'admission_problem': captured.viability_problem(case.files, budget)})
    return {'evidence': 'plan-only', 'provider_gate': 'not-run', 'runs': rows,
        **({'provider_routes': provider_routes} if provider_routes else {}),
        'conditions': list(configured), 'cases': len(cases),
        'protocol': {'question_budget': budget, 'answered_turns': budget if complete else 4, 'maximum_same_question_replies': 1,
            'script_version': 'approach-grounded-v2', 'focused_response_contract': 'nested-result-v2',
            'preparation': 'identical locally validated synthetic maps; no provider mapping call',
            'coaching': ('funded overview and all bounded answer sections' if complete else
                         'protected funds retained; no provider coaching call'),
            'processing': ('interactive 45-second processing cap; existing coaching 90-second request deadline'
                           if complete else 'same current 45-second policy in all conditions'),
            'order': ('fixed four-case order, one attempt each; no statistical speed comparison' if complete else
                      'conditions rotated per case; one repeat is exploratory, not a power claim'),
            'baseline': 'none; candidate completion gate' if complete else 'previous separate/full OpenRouter policy, not GPT Luna',
            'quality': 'manual review required for every role and condition',
            'notes': 'identical sources/answer scripts; adaptive dialogue paths may differ'},
        'ordinary_bound_nano': sum(row['ordinary_bound_nano'] for row in rows)}


def run_case(case, condition, policy, observer, *, evidence, on_measure=None, complete=False):
    """Exercise actual typed/provider contracts in isolated benchmark scopes."""
    budget = 8 if complete else 5
    session = ResearchDefenseSession.create(case.plan(), budget, 'mixed' if case.mixed else 'research', 'proposal')
    identity = secrets.token_hex(12)
    scope = 'benchmark-run:'+identity
    captured = policy.snapshotted(case.files, budget)
    problem = captured.viability_problem(case.files, budget)
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
    metadata['response_contract'] = 'flat-v1' if captured.evidence_policy == EVIDENCE_FULL else 'nested-result-v2'
    records, quality = [], []
    coaching = None
    coaching_reports = []
    from backend.question_generator import RESEARCH_PANELISTS

    def measure(phase, action, answer_index=None):
        operation = secrets.token_hex(16)
        outgoing = session.turns[-1].panelist if session.turns else None
        observer.context = {**metadata, 'operation_id': operation, 'outgoing_role': outgoing}
        bind_operation(operation)
        started = monotonic()
        result = None
        failure = None
        reason = None
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
            reason = failure_code(error)
        elapsed = round((monotonic()-started)*1000)
        supplied = take_supplied_usage(operation)
        stages, _ = observer.snapshot()
        stages = [r for r in stages if r.get('operation_id') == operation]
        record = {**metadata, 'event': 'total', 'kind': 'coaching' if phase == 'coaching' else 'transition',
            'operation_id': operation,
            'phase': 'completion' if session.completed and phase != 'coaching' else phase, 'duration_ms': elapsed,
            'outgoing_role': outgoing, 'request_count': len(stages),
            'automatic_retries': sum(text.startswith('Trying again') for _,text in statuses),
            'retry_wait_ms': round(sum((statuses[i+1][0] if i+1<len(statuses) else monotonic())-stamp
                for i,(stamp,text) in enumerate(statuses) if text.startswith('Waiting to retry'))*1000),
            'outcome': 'failed' if failure else 'same_question' if isinstance(result, str) and
                result in {'clarified', 'probed'} else 'succeeded',
            **({'failure_class': failure, 'failure_code': reason,
                'failure_stage': stages[-1]['stage'] if stages else 'before_dispatch'} if failure else {})}
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
            **({'failure_code': reason, 'failure_stage': record['failure_stage']} if failure else {}),
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
            for _ in range(budget if complete else 4):
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
        if complete and session.completed:
            from backend.coaching_progress import CoachingInput, CoachingProgress
            from backend.question_generator import generate_coaching_report
            from backend.research_coaching import validate_complete
            history = tuple(session.coaching_history())
            coaching = CoachingProgress(CoachingInput(tuple(case.files), history, session.context(),
                session.defense_type, session.research_stage,
                provider_scope=scope, provider_owner=practice.owner))
            for section in coaching.sections:
                def coach(notify):
                    coaching.begin(section)
                    notify('Preparing coaching…')
                    report = generate_coaching_report(list(case.files), list(history), None,
                        client=practice.client(session, case.files).coaching(),
                        defense_type=session.defense_type, research_stage=session.research_stage,
                        research_context=session.context(), overview_only=section.turns is None,
                        section_turns=section.turns)
                    coaching.accept(section, report)
                    coaching_reports.append({'section': section.id,
                        **{key: getattr(report, key) for key in
                           ('summary', 'strengths', 'improvements', 'next_step', 'closing')},
                        # Original contributions remain in the synthetic scripts,
                        # never copied into timing/quality exports.
                        'answer_cards': [{'probe_id': (card.get('probe') or {}).get('id'),
                            **{key: card[key] for key in ('turn', 'feedback', 'probe_feedback')}}
                            for card in (report.answer_cards or [])]})
                    if coaching.complete_sections:
                        validate_complete(coaching.assembled(), history, session.defense_type, batched=True)
                        coaching.completion_status = 'ready'
                if not measure('coaching', coach):
                    section.status = 'failed'
                    break  # No unapproved manual section retry in this campaign.
        if complete and quality:
            roles = sorted({turn.panelist for turn in session.turns})
            quality[-1]['run_result'] = {
                'defense_complete': session.completed, 'completion_reason': session.completion_reason,
                'questions': len(session.turns), 'question_budget': budget,
                'accepted_answers': sum(bool(turn.answer) for turn in session.turns),
                'pending_submission_retained': flow.pending is not None,
                'recovery_stage': practice.question_recovery.stage,
                'roles_observed': roles, 'roles_missing': sorted(set(RESEARCH_PANELISTS)-set(roles)),
                'coaching_complete': coaching is not None and coaching.completion_status == 'ready',
                'cards_ready': coaching.snapshot()['cards_ready'] if coaching else 0,
                'cards_required': len(session.coaching_history()),
                'coaching_sections': coaching.snapshot()['sections'] if coaching else [],
                'coaching_reports': coaching_reports,
                'manual_quality_gate': 'unreviewed'}
            if on_measure:
                on_measure(records, quality)
    practice.cancel()
    return records, quality


def run_campaign(observer, *, evidence, on_case=None, cases=CASES, configured=None, complete=False):
    records, quality = [], []
    configured = policies() if configured is None else configured
    conditions = list(configured)
    for index, case in enumerate(cases):
        order = conditions[index % len(conditions):] + conditions[:index % len(conditions)]
        for condition in order:
            rows, review = run_case(case, condition, configured[condition], observer, evidence=evidence,
                on_measure=(lambda new, review: on_case(records+new, quality+review)) if on_case else None,
                complete=complete)
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
    parser.add_argument('--cases', nargs='+', choices=[case.id for case in CASES], help='built-in synthetic cases only')
    parser.add_argument('--conditions', nargs='+', choices=list(policies()), help='captured comparison conditions')
    parser.add_argument('--provider-comparison', action='store_true',
                        help='compare current routing against DeepInfra for DeepSeek only; fixed reasoning')
    parser.add_argument('--complete-candidate', action='store_true',
                        help='attempt full eight-question candidate defenses and protected coaching')
    args = parser.parse_args(argv)
    if args.provider_comparison and args.conditions:
        parser.error('--provider-comparison has its own fixed conditions')
    if args.complete_candidate and (args.conditions or args.provider_comparison):
        parser.error('--complete-candidate has its own fixed condition and routes')
    cases = tuple(case for case in CASES if args.cases is None or case.id in args.cases)
    configured = {name: policy for name, policy in policies().items()
                  if args.conditions is None or name in args.conditions}
    routes = None
    if args.provider_comparison:
        configured, routes = provider_comparison()
    if args.complete_candidate:
        configured, routes = complete_candidate()
    plan = measurement_plan(cases, configured, provider_routes=routes, complete=args.complete_candidate)
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
        if args.complete_candidate:
            report['run_results'] = [{key: item[key] for key in
                ('case_id', 'condition', 'run_id', 'run_result')} for item in quality if 'run_result' in item]
        observed = {(r['case_id'], r['condition']) for r in records}
        report['not_run'] = [{'case_id': row['case_id'], 'condition': row['condition']}
                             for row in plan['runs'] if (row['case_id'],row['condition']) not in observed]
        (args.output/'report.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    with local_ledger(args.output):
        observer = CampaignObserver(secrets.token_hex(16), int(cap*1_000_000_000), policies()['current'],
                                    provider_routes=routes)
        records, quality, active = run_campaign(observer, evidence='actual-provider', on_case=write,
                                               cases=cases, configured=configured, complete=args.complete_candidate)
        # run_campaign returns stage rows too; write takes transition rows only.
        write([r for r in records if r['event'] == 'total'], quality)
    print('Evidence written. Provider gate remains unreviewed; no production setting was changed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
