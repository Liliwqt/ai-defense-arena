"""Synthetic context-size/coverage selection. No provider requests or private inputs.

Run from repository root: .venv/bin/python -m tests.evidence_context_harness
This measures serialized evidence bytes, never model speed or semantic quality.
"""
from dataclasses import replace
import json

from backend.focused_evidence import EvidenceLimits, FocusedEvidence
from backend.project_files import ProjectFile
from backend.question_generator import GroundedQuestion


def measure():
    records = []
    for field in ('qualitative', 'theoretical', 'mixed', 'unclear'):
        files = []
        refs = []
        for document in range(3):
            lines = [f'Background discussion for {field}, document {document}, line {n}.' for n in range(1, 601)]
            filename = f'{field}-{document}.md'
            for n in (120, 240, 360):
                lines[n-1] = f'Essential {field} argument document {document} at passage {n}.'
                refs.append({'filename':filename,'evidence_line':n,'evidence_text':lines[n-1]})
            lines[549] = f'Longitudinal retention comparison for {field} at twelve weeks.'
            files.append(ProjectFile(filename,'\n'.join(lines),'research_text'))
        if field == 'mixed':
            files.insert(0, ProjectFile('analysis.py','def compare(values):\n    return sorted(values)\n'))
        context = {'plan':{'id':'synthetic-confirmed-'+field,'profile':{'approaches':[field]},
                          'topics':[{'id':'chosen','references':refs}]},'selected_topic':'chosen'}
        for count in (4, 8, 14):
            limits = replace(EvidenceLimits(),excerpts=count)
            evidence = FocusedEvidence.build(files,context=context,defense_type='mixed' if field=='mixed' else 'research',limits=limits)
            before = evidence.render()
            matched = sum(ref['evidence_text'] in before for ref in refs)
            expansion = evidence.expand('longitudinal retention twelve weeks')
            records.append({'case':field,'excerpt_limit':count,'required_passages':len(refs),
                            'retained_passages':matched,'accepted_source_bytes':sum(len(f.content.encode()) for f in files),
                            'focused_bytes':len(before.encode()),'expanded_bytes':len(evidence.render().encode()),
                            'lookup_bytes':expansion['bytes'],'lookup_windows':expansion['windows']})
    return records


if __name__ == '__main__':
    print(json.dumps(measure(),indent=2))
