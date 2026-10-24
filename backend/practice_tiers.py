"""Server-owned practice tiers; a free room never upgrades itself to paid AI."""

STANDARD = 'standard'
FREE = 'free'
FREE_MODEL = 'dots-studio/dots-3-note-preview:free'
FREE_PROVIDER = 'atlas-cloud'
FREE_CONTEXT_TOKENS = 512000
RETIRED_FREE_MODEL = 'nvidia/nemotron-3.5-super-vl:free'
FREE_QUESTION_LIMIT = 8


def validate_tier(value):
    if value not in {STANDARD, FREE}:
        raise ValueError('Choose Free practice or Standard practice.')
    return value


def validate_tier_budget(tier, budget):
    if tier == FREE and budget > FREE_QUESTION_LIMIT:
        raise ValueError(f'Free practice supports up to {FREE_QUESTION_LIMIT} questions per defense.')
    return budget
