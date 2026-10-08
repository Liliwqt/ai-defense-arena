# Recover missed live payment notifications with verified provider reads

Status: accepted design, 2026-10-08; implementation pending.

Webhook-only settlement can leave a legitimately paid receipt pending when
notification delivery is exhausted. The user chose automatic server recovery
rather than requiring an operator to resend every missed webhook. Signed
webhooks remain primary; independent authenticated provider retrieval may
settle the exact bound live receipt only after validating mode, account/receipt
binding, intent/payment identity, amount and currency through the same
transactional once-only award boundary. Browser status, redirects and payer
claims never authorize an award.

This explicitly supersedes ADR 0001's webhook-only restriction for live recovery,
not its sandbox policy or dynamic QR choice. Duplicate webhook/recovery races
must not award twice; uncertain provider results remain unresolved rather than
being treated as paid. Recovery requires bounded server work and audit evidence,
not a new credit-awarding browser endpoint.
