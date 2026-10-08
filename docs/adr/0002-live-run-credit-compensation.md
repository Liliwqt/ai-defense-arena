# Return credits for server-interrupted paid defenses

Status: accepted design, 2026-10-08; implementation pending.

Rooms are currently lost on a server restart, while completed and unfinished
charged runs cannot be distinguished in durable records. The user chose an
automatic, once-only return of the ten charged credits for a verified server
interruption of an unfinished paid run, rather than requiring a support request.
This requires durable run outcomes and compensation records so completed runs,
explicit user endings and temporary browser disconnects are not refunded; it
restores credits without reversing the original real-money top-up payment.

The user also chose included retries after a later question-generation failure,
with an explicit option to end the run and return its ten credits once while
that server-recorded error remains unresolved. Ordinary ending, answer timeout
and completed defenses do not qualify; this is distinct from a payment refund.

A run becomes abandoned after all defenders are disconnected for ten minutes,
with no automatic credit return. This must be observed while the service is
operating; service downtime must not be misclassified as a user's abandonment.

The user subsequently extended included retries and explicit ending with the
ten-credit return to an unresolved server-recorded final coaching error, because
coaching is part of the purchased service. Finished questions alone do not mark
that failed service successfully completed. An error-based return ends the run
and is once-only; stale AI results cannot revive it or produce a second charge.
