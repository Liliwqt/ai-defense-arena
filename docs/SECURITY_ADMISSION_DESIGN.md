# Room, mobile sign-in and AI resource limits

Status: interview superseded by To Spec, 2026-10-08. No remediation implemented.

The user requested synthesis before answering the Round 1 policy questions. The local [implementation specification](../.scratch/security-admission/spec.md) is ready-for-agent with explicit proposed defaults. The user confirmed its test boundaries; no interview answer, numeric-policy approval, implementation or deployment is implied. This note remains the discovery record rather than a competing specification.

## Evidence and boundaries

The completed Codex Security functional review found three medium resource-exhaustion issues in the feature working tree at dd037d5: a signed-in account can consume the shared 20-room capacity; anonymous requests can fill the 128 native sign-in handoffs; and selected defenders can trigger paid interpretation after the two-clarification allowance is exhausted. These are source-validated findings, not demonstrated credit theft or account takeover. The review was static/offline; live ingress/provider behavior was not verified.

Preserve server-verified host ownership, guest tokens, exact citations, speaker selection, voting and answer deadlines, same-question clarifications, code-only four-to-eight turns, and research budgets up to 100 questions. Private chat stays excluded from AI context. The flat ten-credit run charge and existing interruption/error credit-return contract are not being repriced. Main and production remain unchanged during design.

## Decision tree

### Round 1 — open policy choices

1. Room fairness: define how many rooms one host may keep, independently of the existing one-active-run rule.
   - Then settle idle-lobby and finished-room retention, explicit close behavior, reconnect expiry notices, cleanup safety and creation throttling.
2. Mobile sign-in admission: decide whether limits combine individual attempts and network-level protection, while tolerating shared school/mobile networks.
   - Then settle retry reuse, expiry, request budgets, trusted client identification and recovery messages.
3. Clarification allowance: decide the submission behavior after the two existing clarifications are consumed.
   - Then settle pre-provider attempt limits, included retries, total clock-pause allowance, guest/host accounting and run budgets that scale with approved research length.

No answers have been accepted yet. Recommendations presented during the interview are proposals, not decisions.

## Verification to specify

Read-only source cross-check confirms that the room ceiling is checked after upload parsing, room abandonment retains the room entry, and native clients depend on verifier/challenge binding and retry after session-store failure. Admission must therefore be enforced before expensive work where possible. Room cleanup must distinguish terminal retention from active-run settlement. Existing native request compatibility and saved-answer recovery must be considered when specifying the changes.

Use deterministic offline tests for room fairness/cleanup, anonymous admission and legitimate native retries, and AI budgets enforced before provider calls. Include concurrent requests, reconnect, retained answers and stale results. Record real shared-network/native-device behavior separately; mocked tests cannot establish hosted proxy configuration or live AI quality.
