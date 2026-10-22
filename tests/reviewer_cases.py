"""Built-in synthetic research only; no uploaded papers or arbitrary file input."""
from dataclasses import asdict, dataclass, replace
import hashlib
import json
from types import SimpleNamespace

from backend.openrouter_questions import (
    RunQuestionPolicy, SEPARATE_PLANNING, EVIDENCE_FULL,
)
from backend.project_files import ProjectFile
from backend.question_generator import RESEARCH_PANELISTS
from backend.research_plan import generate_research_plan


@dataclass(frozen=True)
class ReviewerCase:
    id: str
    field: str
    approach: str
    language: str
    mixed: bool = False
    long: bool = False

    @property
    def files(self):
        methods = {
            'quantitative': 'Compare paired baseline and pilot waiting times; report uncertainty without causal claims.',
            'qualitative': 'Interview volunteers and analyze contrasting accounts; retain an audit trail and negative cases.',
            'theoretical': 'Distinguish necessary from sufficient assumptions using a counterexample; no experiment is claimed.',
            'computational/design': 'Compare paired benchmark inputs with a documented baseline and report failed runs.',
        }
        source = '\n'.join([
            f'Synthetic {self.field} proposal.',
            'Aim: explain a bounded contribution; completed results are not available.',
            f'Study approach: {self.approach}.', methods[self.approach],
            'Ethics: participation is voluntary where people are involved; minimize identifying data and attribute sources.',
            'Impact: the contribution is limited to the stated setting and must be evaluated before generalizing.',
            'Limitations: selection assumptions and alternative explanations remain; no effectiveness is proven.',
            'Setting: a proposed local study; the host description does not replace these source statements.',
        ])+'\n'
        if self.long:
            source += '\n'.join(f'Background note {n}: describe the proposed scope without claiming new findings.' for n in range(450))+'\n'
        source += 'Eligibility protocol: preserve excluded cases and justify assumptions against the original comparison.\n'
        files = [ProjectFile('synthetic-study.md', source, 'research_text')]
        if self.mixed:
            files.append(ProjectFile('synthetic-evaluation.py', 'def compare(baseline, pilot):\n    return pilot - baseline\n'))
        return files

    @property
    def answers(self):
        if self.language == 'modern-bisaya':
            return (
                'Base sa proposed method, mag-compare mi gamit ang documented baseline. Wala pa mi results, so dili pa mi mo-claim nga effective na. Bisaya lang.',
                'Voluntary ang participation kung naay participants. Gamay ra nga personal data ang kuhaon, ug i-attribute namo ang sources.',
                'Sa stated setting pa lang among claim. Kinahanglan pa namo i-evaluate ang contribution before mi mo-generalize.',
                'I-document namo ang excluded cases ug assumptions. Tan-awon pud namo ang alternative explanations; proposal pa ni.',
            )
        return (
            'We will follow the stated comparison or argument and document its assumptions. This is a proposal, so we have no results establishing effectiveness.',
            'Participation will be voluntary where relevant. We will minimize identifying information and attribute our sources.',
            'We limit the contribution to the stated setting and will evaluate it before generalizing.',
            'We will document excluded cases, justify assumptions and examine alternative explanations without claiming completed findings.',
        )

    @property
    def fingerprint(self):
        data = [asdict(self), [(f.name, f.content, f.kind) for f in self.files], self.answers]
        return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

    def plan(self):
        output = {'topics': [
            {'title': title, 'objective': objective, 'panelist': role,
             'references': [{'source_file': 1, 'evidence_line': line}], 'gaps': []}
            for title, objective, role, line in zip(
                ('Research reasoning', 'Research integrity', 'Contribution and scope', 'Assumptions and limits'),
                ('Justify the stated method or argument.', 'Explain the applicable safeguards and attribution.',
                 'Justify the bounded contribution.', 'Examine an assumption or alternative explanation.'),
                RESEARCH_PANELISTS, (4, 5, 6, 7))],
            'uncertainties': ['No completed results are supplied.'],
            'profile': {'fields': [self.field], 'approaches': [self.approach],
                'setting': 'Proposed local study', 'explanation': 'The source explicitly describes the proposed approach.',
                'references': [{'source_file': 1, 'evidence_line': 3}], 'uncertainties': []}}
        class Fixture:
            @property
            def responses(self): return self
            def parse(self, **kwargs): return SimpleNamespace(output_parsed=output)
        # Validate the supplied map/citations locally; preparation AI is outside
        # the interactive comparison and is never called by this harness.
        return generate_research_plan(self.files, None, client=Fixture(),
            defense_type='mixed' if self.mixed else 'research', research_stage='proposal')


CASES = (
    ReviewerCase('quantitative-en', 'Service operations', 'quantitative', 'english'),
    ReviewerCase('qualitative-bisaya', 'Education', 'qualitative', 'modern-bisaya'),
    ReviewerCase('theoretical-long-en', 'Applied philosophy', 'theoretical', 'english', long=True),
    ReviewerCase('mixed-long-bisaya', 'Software evaluation', 'computational/design', 'modern-bisaya', mixed=True, long=True),
)


def policies():
    current = RunQuestionPolicy.configured('standard')
    baseline = replace(current, planning_contract=SEPARATE_PLANNING,
                       evidence_policy=EVIDENCE_FULL, evidence_limits=None)
    roles = RESEARCH_PANELISTS
    candidate = replace(current, reviewer_reasoning={
        roles[0]: {'effort': 'low'}, roles[1]: {'effort': 'low'},
        roles[2]: {'max_tokens': 512}, roles[3]: {'effort': 'low'}},
        interaction_reasoning={**current.interaction_reasoning, roles[2]: {'max_tokens': 512}},
        planner_output_tokens=2048, reviewer_output_tokens=4096, combined_output_tokens=4096)
    return {'baseline': baseline, 'current': current, 'candidate-light': candidate}
