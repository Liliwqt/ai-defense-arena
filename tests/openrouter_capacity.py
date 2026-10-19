"""Opt-in synthetic request-size measurements, never live inference.

Run from the repository root: .venv/bin/python -m tests.openrouter_capacity
Outputs conservative bounds and context/Start gates, not measured token bills.
"""

from dataclasses import asdict
import json
from types import SimpleNamespace

from backend.openrouter_questions import CONTEXT_TOKENS, FRAMING_BYTES, RunQuestionPolicy
from backend.openrouter_stream import payload
from backend.project_files import ProjectFile, MAX_TOTAL_BYTES
from backend.question_generator import AnsweredQuestion, PanelistProbe, CoachingDraft, CoachingPoint, generate_coaching_report


class CaptureOverview:
    def __init__(self, policy):
        self.policy = policy
        self.responses = self
        self.input_bound = None

    def parse(self, *, input, text_format, **unused):
        body = payload(self.policy.coaching_model, input, text_format,
            reasoning=self.policy.coaching_reasoning, max_tokens=self.policy.coaching_output_tokens)
        self.input_bound = len(json.dumps({'messages': input, 'schema': body['response_format']}, ensure_ascii=False).encode()) + FRAMING_BYTES
        return SimpleNamespace(output_parsed=CoachingDraft(summary='Synthetic scope discussion.',
            strengths=[CoachingPoint(turn=0, text='The defender stated a scope.')], improvements=[], next_step='Practice the scope.'))


def measure():
    rows = []
    for size in (5_000, 60_000, 300_000, MAX_TOTAL_BYTES):
        files = [ProjectFile('synthetic.md', 'Synthetic accepted paper.\n' + 'x' * (size - 26), 'research_text')]
        for budget in (4, 12, 100):
            policy = RunQuestionPolicy().snapshotted(files, budget)
            history = [AnsweredQuestion('Methodology Reviewer', f'Explain decision {i+1}?', 'a' * 4000,
                probe=PanelistProbe(f'probe-{i}', 'Which baseline?', status='answered', reply='b' * 4000))
                for i in range(budget)]
            capture = CaptureOverview(policy)
            generate_coaching_report(files, history, None, client=capture,
                defense_type='research', research_stage='proposal', overview_only=True)
            rows.append({'source_bytes': sum(len(file.content.encode()) for file in files), 'question_budget': budget,
                'start_viable_default_5_usd': policy.viability_problem(files, budget) is None,
                'estimated_required_nano_usd': policy.coaching_reserve_nano + policy.question_bound(files, budget),
                'protected_coaching_nano_usd': policy.coaching_reserve_nano,
                'overview_serialized_input_bound': capture.input_bound,
                'overview_request_fits_context': capture.input_bound + policy.coaching_output_tokens <= CONTEXT_TOKENS,
                'overview_reservation_nano_usd': policy.stage_bound(capture.input_bound, policy.coaching_output_tokens)})
    return {'kind': 'offline UTF-8 serialization and conservative bounds; no live tokens, latency, quality or billing',
            'policy': asdict(RunQuestionPolicy()), 'rows': rows}


if __name__ == '__main__':
    print(json.dumps(measure(), indent=2))
