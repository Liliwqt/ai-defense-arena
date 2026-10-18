# Retain bounded opening history without archiving defense runs

Status: accepted design, confirmed with the consolidated plan on 2026-10-17; implementation pending.

Fresh research defenses otherwise lose previous opening context, so retain only the latest five committed opening questions per host and accepted paper content for 30 days, independently of in-memory rooms. Content identity preserves history across renamed uploads; account scope and bounded retention avoid making this a shared corpus or a full paper/answer/audio archive. Record openings idempotently at their authoritative commit, reject stale/unaccepted candidates, and preserve source validation and once-only charging when the host retries or explicitly accepts repetition.
