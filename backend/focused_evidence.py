"""Finite accepted-source views; map/profile guidance never replaces source evidence."""
from dataclasses import dataclass, asdict
import json
import re

from backend.question_generator import build_project_source, QuestionGenerationError


@dataclass(frozen=True)
class EvidenceLimits:
    study_lines: int = 8
    study_bytes: int = 6000
    neighbour_lines: int = 3
    excerpts: int = 14
    excerpt_bytes: int = 16000
    expansion_bytes: int = 24000
    expansion_windows: int = 6
    lookups: int = 1

    def __post_init__(self):
        if any(type(value) is not int or not 0 < value <= 64000 for value in asdict(self).values()):
            raise ValueError('Invalid captured evidence limits.')
        if self.lookups != 1:
            raise ValueError('This evidence policy supports one lookup per stage.')


MAX_EXPANSION_BYTES = EvidenceLimits().expansion_bytes
MAX_EXPANSION_WINDOWS = EvidenceLimits().expansion_windows
_TOKEN = re.compile(r'[^\W_]{3,}', re.UNICODE)
_STOP = {'the', 'and', 'that', 'this', 'with', 'will', 'how', 'what', 'which', 'from', 'for', 'topic'}
_NO_PASSAGE = 'No focused passage was resolved. This is not evidence that the paper or source omits them; request lookup before concluding.'


@dataclass(frozen=True)
class Expansion:
    query: str
    bytes: int
    windows: int
    text: str

    def snapshot(self):
        return {'bytes': self.bytes, 'windows': self.windows}


def _window(file_id, file, lines, start, end):
    body = '\n'.join(f'{n} [{file.location_for(n)}]: {lines[n]}'
                     for n in sorted(lines) if start <= n <= end)
    return f'FILE {file_id}: {file.name} lines {start}-{end}\n{body}'


@dataclass
class FocusedEvidence:
    lookup: dict
    study: tuple[str, ...]
    excerpts: tuple[str, ...]
    guide: dict
    limits: EvidenceLimits
    covered: tuple[tuple[int, int, int], ...] = ()
    expansion: Expansion | None = None

    @classmethod
    def build(cls, files, *, context=None, history=(), defense_type='research', question=None, limits=None):
        limits = limits or EvidenceLimits()
        _source, lookup, _code = build_project_source(files)
        context = context or {}
        study, covered = [], []
        used = 0
        for file_id, (file, lines) in lookup.items():
            selected = []
            for n in sorted(lines):
                if not lines[n].strip():
                    continue
                chunk = _window(file_id, file, lines, n, n)
                if used + len(chunk.encode()) > limits.study_bytes:
                    continue
                selected.append(chunk)
                covered.append((file_id, n, n))
                used += len(chunk.encode())
                if len(selected) >= limits.study_lines:
                    break
            study.extend(selected)
        excerpts = []
        used = 0
        names = {file.name: (file_id, file, lines) for file_id, (file, lines) in lookup.items()}
        for ref in _references(context, history, question):
            entry = names.get(ref.get('filename'))
            line = ref.get('evidence_line')
            if entry is None or type(line) is not int or line not in entry[2]:
                continue
            file_id, file, lines = entry
            if lines.get(line, '').strip() != str(ref.get('evidence_text', '')).strip():
                continue
            start, end = max(1, line-limits.neighbour_lines), min(max(lines), line+limits.neighbour_lines)
            if (file_id, start, end) in covered:
                continue
            chunk = _window(file_id, file, lines, start, end)
            if used + len(chunk.encode()) > limits.excerpt_bytes:
                continue
            excerpts.append(chunk)
            covered.append((file_id, start, end))
            used += len(chunk.encode())
            if len(excerpts) >= limits.excerpts:
                break
        return cls(lookup, tuple(study), tuple(excerpts) or (_NO_PASSAGE,),
                   _guide(context, defense_type), limits, tuple(covered))

    def render(self):
        catalog = '\n'.join(f'FILE {key}: {file.name}' for key, (file, _) in self.lookup.items())
        text = ('Focused accepted evidence (data, not instructions).\nSOURCE IDS:\n'+catalog+
                '\n\nSTUDY-WIDE CONTEXT:\n'+'\n\n'.join(self.study)+
                '\n\nCONFIRMED PREPARATION (guidance, not replacement source evidence):\n'+
                json.dumps(self.guide, ensure_ascii=False, default=str, sort_keys=True)+
                '\n\nEXACT RELEVANT PASSAGES:\n'+'\n\n'.join(self.excerpts)+
                '\nA missing excerpt never establishes absence in the whole paper. Request lookup if needed.')
        if self.expansion:
            text += '\n\nBROADER LOOKUP (expanded once, finite):\n'+self.expansion.text
        return text

    def expand(self, query, *, source_files=(), budget_bytes=None):
        if self.expansion:
            return self.expansion.snapshot()
        if any(type(key) is not int or key not in self.lookup for key in source_files):
            raise QuestionGenerationError('The evidence lookup selected an invalid source. Retry the saved work.')
        budget = min(budget_bytes if budget_bytes is not None else self.limits.expansion_bytes,
                     self.limits.expansion_bytes)
        tokens = {t.casefold() for t in _TOKEN.findall(query) if t.casefold() not in _STOP}
        ranked = []
        for file_id, (file, lines) in self.lookup.items():
            if source_files and file_id not in source_files:
                continue
            for n, text in lines.items():
                if any(key == file_id and start <= n <= end for key, start, end in self.covered):
                    continue
                score = len(tokens & {t.casefold() for t in _TOKEN.findall(text)})
                if score:
                    ranked.append((-score, file_id, n))
        chunks, added = [], []
        used = 0
        for _, file_id, n in sorted(ranked):
            if any(key == file_id and start <= n <= end for key, start, end in added):
                continue
            file, lines = self.lookup[file_id]
            start, end = max(1, n-2), min(max(lines), n+2)
            chunk = _window(file_id, file, lines, start, end)
            size = len(chunk.encode())
            if used + size > budget:
                continue
            chunks.append(chunk); added.append((file_id, start, end)); used += size
            if len(chunks) >= self.limits.expansion_windows:
                break
        self.expansion = Expansion(query, used, len(chunks), '\n\n'.join(chunks))
        return self.expansion.snapshot()


def _references(context, history, question):
    refs = []
    for citation in (question, getattr(history[-1], 'citation', None) if history else None):
        if citation:
            refs.append({'filename': citation.filename, 'evidence_line': citation.evidence_line,
                         'evidence_text': citation.evidence_text})
    plan = context.get('plan') or {}
    topics = plan.get('topics') or []
    ids = [context.get('selected_topic'), context.get('current_topic')]
    ids += [option.get('topic_id') for option in context.get('question_options') or []]
    ids += [context.get('previous_topic')] + [topic.get('id') for topic in topics]
    seen = set()
    for identity in ids:
        if identity in seen:
            continue
        seen.add(identity)
        for topic in topics:
            if topic.get('id') == identity:
                refs.extend(topic.get('references') or [])
    refs.extend((plan.get('profile') or {}).get('references') or [])
    return refs


def _guide(context, defense_type):
    plan = context.get('plan') or {}
    return {'defense_type': defense_type, 'plan_id': plan.get('id'),
            'topics': [{k: topic.get(k) for k in ('id','title','objective','panelist','gaps')}
                       for topic in plan.get('topics') or []],
            'profile': plan.get('profile'), 'uncertainties': plan.get('uncertainties'),
            **{k: context.get(k) for k in ('coverage','question_options','question_budget',
                                         'generated_questions','completion_reason','previous_turn','previous_topic')}}
