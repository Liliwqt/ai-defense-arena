# Focused evidence for interactive research turns

New Standard research/mixed runs capture `focused-v2` and its numerical evidence
limits alongside the existing model and reasoning settings. The planner, question
writer, answer interpretation, clarification and probe paths use the same evidence
builder. Mapping and coaching retain their existing policies. Free and saved
`full-v1` runs retain their earlier source path. An unsupported saved evidence
version enters recovery rather than silently changing an active run's settings.

The evidence view contains numbered source identities, study-wide passages,
confirmed preparation guidance, exact relevant passages and neighboring lines.
Current citations and the selected topic take priority over optional topics.
Conversation, coverage, language and probe history remain in the task prompt.
The map and host profile guide discussion; neither replaces source evidence.
Every returned citation still validates against the complete accepted upload,
including paper-only versus mixed/code eligibility.

## Captured bounds

| Part | Limit |
| --- | --- |
| Study context | Up to 8 nonblank lines per file; 6,000 bytes total |
| Relevant passages | Up to 14 windows; 16,000 bytes total; 3 neighboring lines each side |
| Broader lookup | Once per stage; up to 6 windows and 24,000 bytes |

These bound source excerpts, not the entire serialized request. The source
catalog, preparation and required conversation still contribute to its size.
Each actual serialized request is independently bounded and reserved by the
existing transport before dispatch.

## Explicit lookup and recovery

A provider may return a structured lookup instead of a decision. Mixing lookup
with a decision is invalid. The query searches accepted source lines outside the
initial windows, optionally restricted to valid numeric file IDs. Results retain
the original file/line/page identities. Empty results, an invalid source ID or a
second lookup produce retained-work recovery rather than an invented conclusion.
A missing excerpt never establishes that the paper omits the information.

Lookup uses the same processing deadline, selected model, retry policy and
question allowance as the task. Interpretation also checks the captured deadline
before a continuation can dispatch. Numeric lookup bytes, request count and
duration join available provider usage in content-free operation timing records.
Unknown usage retains its conservative spending hold.

Validated question plans and expanded evidence can survive writer-only recovery.
Their identity covers room/run/turn, accepted content, confirmed preparation,
conversation and policy. Material changes, completion or lifecycle invalidation
clear that cache; obsolete work cannot restore it.

Start admission sizes the ordinary route. Optional lookups, like retries, must
fit the remaining question funds when requested; they cannot borrow the protected
coaching reserve. Admission does not promise funding for every possible lookup
or retry. This avoids reserving a second full-source writer for every question
while preserving exact dispatch-time spending checks.

## Local measurements and evidence limits

Run `.venv/bin/python -m tests.evidence_context_harness` for repeatable synthetic
context measurements. The fixtures place nine required passages across three
sources, including decisive evidence outside the initial view.

| Synthetic case | Accepted source bytes | Focused bytes at 14 windows | Required passages retained |
| --- | ---: | ---: | ---: |
| Qualitative | 109,464 | 8,503 | 9/9 |
| Theoretical | 109,464 | 8,503 | 9/9 |
| Mixed | 98,711 | 7,903 | 9/9 |
| Confirmed unclear | 102,264 | 8,003 | 9/9 |

Limits of 4 and 8 windows retained only 4/9 and 8/9 passages respectively in
these fixtures. The selected limit retained all nine. Broader searches added
three bounded windows (1,179–1,287 bytes). This supports a provisional context
bound; it does not establish actual model comprehension, complete prompt size,
latency or billed savings.

Authenticated two-client tests cover lookup-aware research/mixed defenses,
clarification, probes, repeated/empty/malformed lookup, writer recovery, deadline
expiry, exact citations and protected funds. Providers are mocked. Actual
provider schema compatibility, question quality, speed and costs remain ticket
08 evidence; typed Streamlit optimization is ticket 07.
