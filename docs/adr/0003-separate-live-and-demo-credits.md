# Preserve sandbox balances separately from live credits

Status: accepted design, 2026-10-08; implementation pending.

Existing sandbox awards and the earlier real-payment trial are test/demo
balances, while the main app's new live purchases buy spendable defense access.
The user chose to preserve that history separately rather than turn old demo
awards into promotional live credits. New live balances must be funded by
verified live purchases and tracked independently, so simulated awards and
historical sandbox charges cannot alter real purchased credits.
