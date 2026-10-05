# 06 — Prepare and save a defense from Android

**Status:** ready-for-human

**Blocked by:** 04 — Sign in and host from the Android app.

**What to build:** An Android host uses native document selection to create
code/research rooms, confirms the research map/budget, completes a defense and
saves/shares its transcript. Existing sandbox checkout opens externally and
returns to server-verified Account state. This slice establishes the narrow
trusted-site export/checkout-return contracts for both shells.

- [ ] System picking supports the existing multiple project files/ZIP and
  research-document inputs, cancellation and retry. Existing extraction/size
  limits, settings and measured progress remain visible and authoritative.
- [ ] Code and research/mixed preparation flows work from picked fixtures,
  with accepted metadata, extraction errors and research budget confirmation.
- [ ] Transcript export/save/share works for the existing summary, including
  browser Blob exports. Only trusted top-level site actions can invoke the
  narrow bridge; no general native execution or private-content logging.
- [ ] Sandbox checkout stays account-owned, opens appropriately outside the
  WebView and returns to refreshed Account state. Redirects cannot award
  credits; existing verified-webhook/deduplication/charging rules remain intact.
- [ ] Cancelled picker/share/checkout and interrupted app return are recoverable
  without losing the current room or causing duplicate paid runs/purchases.
- [ ] Fixture/mocked flow checks and device file/share checks are recorded;
  actual provider simulator checks are separate and never use a real wallet.

## Comments

2026-10-06: User approved this breakdown and requested implementation. Canonical specification: portrait website and downloadable WebView apps.

2026-10-06 implementation handoff: Android document picker/cancellation/multiple selection, origin-bound summary save and external HTTPS checkout/resume source implemented and APK builds. Browser summary/return checks pass with providers mocked; native device checks pending. Unchecked native criteria are not claimed complete.
