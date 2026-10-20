# Standard and Free model audit

Checked 2026-10-20. This is a source/configuration audit plus live read-only public
catalog/endpoint checks, not an inference benchmark. No API key, uploaded paper,
new model generation or account setting was accessed/changed.

## Verdict

The local integration passes its offline gates, but neither tier is fully
validated for live release. The selected Standard models have advertised routes
and compatible reasoning controls. Free practice still depends on a single
Phala endpoint that returned HTTP 429 in the last verified hosted observation.
No subsequent successful Free defense was verified. New GLM mapping, extended
mapping timeout and clearer 429 diagnostics remain local and unpublished.

## Standard assignments

Source: backend/openrouter_mapping.py and backend/openrouter_questions.py.

| Task | Local model/settings | Audit result |
| --- | --- | --- |
| New mapping | z-ai/glm-5.3-flash, low | Advertised effort and structured-output routes exist; actual map quality/speed pending. |
| Planner | z-ai/glm-5.3-flash, low | Catalog supports low; mandatory reasoning makes explicit effort appropriate. |
| Methodology | deepseek/deepseek-v4.1-flash-1017, high | High and low interaction effort are supported; long output can still increase latency. |
| Ethics | anthropic/claude-haiku-5.5, medium | Medium/low supported; base-price routes fit caps, with a large-input price caveat. |
| Impact | qwen/qwen3.8-flash, requested reasoning max_tokens 2048 | Catalog explicitly advertises token-budget reasoning; actual schema/privacy-route compatibility needs account testing. |
| Critical | z-ai/glm-5.3-flash, high | High/low supported; latency has not been measured for the app's questions. |
| Overview/cards | anthropic/claude-haiku-5.5, high | High supported; same large-input pricing caveat as Ethics. |

The catalog reports DeepSeek efforts max/high/low/none; GLM max/high/low; Haiku
max/xhigh/high/medium/low/none. Qwen advertises supports_max_tokens rather than
named efforts. No selected model had an expiration date in the checked catalog.
[OpenRouter catalog](https://openrouter.ai/api/v1/models)

At base prices, advertised strict-output endpoints exist below the application's
$0.30/M input and $1.20/M output caps. This is candidate screening: status zero,
parameter flags and base prices do not prove the full request passes account
privacy settings, dynamic price tiers or the application's actual schema.
[DeepSeek endpoints](https://openrouter.ai/api/v1/models/deepseek/deepseek-v4.1-flash-1017/endpoints),
[GLM endpoints](https://openrouter.ai/api/v1/models/z-ai/glm-5.3-flash/endpoints),
[Haiku endpoints](https://openrouter.ai/api/v1/models/anthropic/claude-haiku-5.5/endpoints),
[Qwen endpoints](https://openrouter.ai/api/v1/models/qwen/qwen3.8-flash/endpoints)

## Remaining Standard limits

1. **Haiku large-input price tier.** The checked base tier is $0.10/M input and
   $0.50/M output. At 100,000 prompt tokens the listed tier becomes $0.50/M and
   $2.50/M; regional routes are higher. Those exceed the unchanged application
   caps. Ethics/coaching requests in that tier can have no eligible route even
   though the advertised context is one million tokens. Do not silently raise
   caps or claim full million-token affordability.
   [Haiku price overrides](https://openrouter.ai/api/v1/models/anthropic/claude-haiku-5.5/endpoints)
2. **Generation deadlines.** Only mapping has the new local 300-second window.
   Funded planner/reviewer/interaction/coaching requests still use a 90-second
   deadline and 15-second read inactivity timeout in QuestionClient._dispatch.
   This is a risk to measure, not proof that every selected role times out.
3. **Conversation quality is untested for the current bundle.** Advertised model
   benchmarks and supported JSON parameters cannot establish grounded research
   questions, useful coaching, or modern Bisaya quality. Full-run testing with
   the exact source and schema is still required.

## Free practice

Source: backend/practice_tiers.py, backend/openrouter_mapping.py,
backend/openrouter_questions.py and backend/provider_allowance.py.

- Mapping, planner, all reviewers and coaching use
  xingchen-agi/xing4.0-29b-a4b:free, pinned to phala.
- Current public endpoint metadata lists one endpoint, zero prompt/completion
  pricing, 262,144 context tokens, structured outputs and reasoning. Phala is
  listed as no-training/zero-retention. These facts do not guarantee capacity.
  [Free endpoint](https://openrouter.ai/api/v1/models/xingchen-agi/xing4.0-29b-a4b:free/endpoints),
  [provider policies](https://openrouter.ai/providers)
- Catalog reasoning metadata does not advertise supports_max_tokens for Xing4.
  The app requests numeric budgets; exact enforcement of those budgets is not
  established by the public flags or mocked tests. Test the actual request
  before promising bounded thinking time.
  [Catalog](https://openrouter.ai/api/v1/models),
  [reasoning controls](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)
- The previously inspected hosted request at 8:32 PM Asia/Manila selected Phala
  and returned 429 after 1.5 seconds. Stored error detail was null. This proves a
  rejected upstream attempt; no daily/minute quota cause or later recovery was
  established. See PROJECT_LOG.md's authenticated 429 inspection entry.
- There is no automatic alternative free model or paid fallback. Current guards
  require a free suffix, zero price caps, no collection and valid citations.
- Free access has no app-credit/voucher requirement, with a 4–8 question budget.
  Default local limits are 15 shared requests/minute, 50/server/day and
  40/owner/day, plus 3 preparation attempts and 80/run requests. Twelve run slots
  are protected for coaching, but they do not reserve upstream or shared daily
  capacity. Clarifications, planner calls, retries and coaching consume requests.
- OpenRouter applies separate account-wide free-model limits, including requests
  made by other applications. Changing rooms or API keys does not reset those
  limits. Another model can help a provider-specific shortage, but not a shared
  daily account cap. [OpenRouter limits](https://openrouter.ai/docs/api_reference/limits)

## Verification and next evidence

Existing owned-source gate: 726 Python tests with AI/Google/payments mocked;
396 React tests and production build from the preceding unchanged frontend gate.
No new runtime changes were made for this audit, so those suites were not rerun.
The tests cover routing, failed requests, retained work, limits and two-client
flows; they do not establish successful hosted inference or quality.

Before calling either tier ready, record a real research/mixed defense from map
through coaching, provider/model used, actual durations and finish reasons,
schema/citation validity, actual usage and all retry paths. Include large-input
Haiku behavior and a successful Free completion. Keep Free labeled as limited
capacity until its demonstrated availability improves. This audit makes no
runtime or publication changes.
