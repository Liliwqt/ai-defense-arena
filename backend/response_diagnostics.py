"""Allowlisted review rejection codes; never serialize response text or inputs."""

REVIEW_REJECTION_CODES = frozenset({
    'submission_missing_result',
    'submission_probe_conflict',
    'submission_probe_payload_invalid',
    'submission_unexpected_probe',
    'submission_answer_has_clarification',
    'submission_missing_assessment',
    'submission_incomplete_selection',
    'submission_clarification_has_plan',
    'submission_invalid_clarification',
    'plan_invalid_assessment',
    'plan_opening_has_assessment',
    'plan_premature_completion',
    'plan_invalid_selection',
    'plan_duplicate_question',
    'plan_invalid_type',
    'evidence_lookup_exhausted',
    'evidence_lookup_empty',
})

SAFE_RESPONSE_CODES = REVIEW_REJECTION_CODES | {
    'evidence_mixed_result', 'evidence_missing_result', 'response_schema_invalid',
}


def classify_rejection(error, code):
    """Keep the original exception class/message and retry policy unchanged."""
    if code not in REVIEW_REJECTION_CODES:
        raise ValueError('Unknown review rejection code.')
    error.reason_code = code
    return error


def safe_response_code(error):
    code = getattr(error, 'reason_code', None)
    return code if isinstance(code, str) and code in SAFE_RESPONSE_CODES else None
