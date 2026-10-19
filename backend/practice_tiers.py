"""Server-owned practice tiers; a free room never upgrades itself to paid AI."""

STANDARD = 'standard'
FREE = 'free'
FREE_MODEL = 'nvidia/nemotron-3.5-super-vl:free'
FREE_QUESTION_LIMIT = 8


def validate_tier(value):
    if value not in {STANDARD, FREE}:
        raise ValueError('Choose Free practice or Standard practice.')
    return value


def validate_tier_budget(tier, budget):
    if tier == FREE and budget > FREE_QUESTION_LIMIT:
        raise ValueError(f'Free practice supports up to {FREE_QUESTION_LIMIT} questions per defense.')
    return budget
