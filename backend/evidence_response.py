"""Versioned lookup alternative for existing structured interactive responses."""
from functools import lru_cache
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, StrictInt, create_model, model_validator

from backend.question_generator import QuestionGenerationError


class EvidenceLookup(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    query: str = Field(min_length=1, max_length=300)
    source_files: list[StrictInt] = Field(default_factory=list, max_length=6)


LOOKUP_GUIDANCE = (
    'Use only accepted evidence for source claims. A missing excerpt is not absence from the paper. '
    'If this evidence cannot support the decision, return lookup with a specific search query and '
    'optional numeric source_files and result null. '
    'Do not guess an answer, coverage status or citation to obtain more context. '
    'Otherwise put the complete normal decision/dialogue in result and set lookup null. '
    'Only one finite lookup is allowed; if it remains insufficient, request lookup again so the '
    'server retains the work for recovery instead of accepting an unsupported decision.'
)


class EvidenceResponseError(QuestionGenerationError):
    """Content-free classification of an unusable evidence response."""
    def __init__(self, code, message):
        self.reason_code = code
        super().__init__(message)


class _EvidenceEnvelope(BaseModel):
    model_config = ConfigDict(extra='forbid')
    _normal_fields: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode='before')
    @classmethod
    def legacy_result(cls, value):
        # Continue validating older flat SDK/test responses with the original
        # domain schema. New provider requests advertise only the envelope.
        if not isinstance(value, dict) or 'result' in value:
            return value
        if not set(value) <= cls._normal_fields | {'lookup'}:
            return value
        lookup = value.get('lookup')
        fields = {key: item for key, item in value.items() if key != 'lookup'}
        if lookup is not None and any(item is not None and item is not False for item in fields.values()):
            raise EvidenceResponseError('evidence_mixed_result', 'The AI mixed an evidence request with a decision. Retry the saved work.')
        return {'lookup': lookup, 'result': None if lookup is not None or not fields else fields}


@lru_cache(maxsize=16)
def lookup_format(schema):
    response = create_model(schema.__name__, __base__=_EvidenceEnvelope,
                            lookup=(EvidenceLookup | None, None), result=(schema | None, None))
    response._normal_fields = frozenset(schema.model_fields) | getattr(schema, 'legacy_response_fields', frozenset())
    return response


def read_result(response, schema):
    """Reject mixed lookup/results; restore the original strict result contract."""
    lookup = response.lookup
    if lookup is not None:
        if response.result is not None:
            raise EvidenceResponseError('evidence_mixed_result', 'The AI mixed an evidence request with a decision. Retry the saved work.')
        return lookup
    if not isinstance(response.result, schema):
        raise EvidenceResponseError('evidence_missing_result', 'The AI returned an incomplete decision. Retry the saved work.')
    return response.result
