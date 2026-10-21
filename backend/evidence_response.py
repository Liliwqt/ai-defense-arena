"""Versioned lookup alternative for existing structured interactive responses."""
from functools import lru_cache
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictInt, ValidationError, create_model

from backend.question_generator import QuestionGenerationError


class EvidenceLookup(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    query: str = Field(min_length=1, max_length=300)
    source_files: list[StrictInt] = Field(default_factory=list, max_length=6)


LOOKUP_GUIDANCE = (
    'Use only accepted evidence for source claims. A missing excerpt is not absence from the paper. '
    'If this evidence cannot support the decision, return lookup with a specific search query and '
    'optional numeric source_files, leaving every decision/dialogue field null or unset. '
    'Do not guess an answer, coverage status or citation to obtain more context. '
    'Otherwise return the normal result with lookup null or absent. '
    'Only one finite lookup is allowed; if it remains insufficient, request lookup again so the '
    'server retains the work for recovery instead of accepting an unsupported decision.'
)


@lru_cache(maxsize=16)
def lookup_format(schema):
    fields = {}
    for name, field in schema.model_fields.items():
        annotation = Annotated[field.annotation, *field.metadata] if field.metadata else field.annotation
        fields[name] = (annotation | None, None)
    return create_model(schema.__name__, __base__=BaseModel,
                        __config__=ConfigDict(extra='forbid'),
                        lookup=(EvidenceLookup | None, None), **fields)


def read_result(response, schema):
    """Reject mixed lookup/results; restore the original strict result contract."""
    lookup = response.lookup
    values = response.model_dump(exclude_unset=True, exclude={'lookup'})
    if lookup is not None:
        if any(value is not None and value is not False for value in values.values()):
            raise QuestionGenerationError('The AI mixed an evidence request with a decision. Retry the saved work.')
        return lookup
    values = {name: value for name, value in values.items()
              if value is not None or schema.model_fields[name].is_required()
              or schema.model_fields[name].default is None}
    try:
        return schema.model_validate(values)
    except ValidationError as error:
        raise QuestionGenerationError('The AI returned an incomplete decision. Retry the saved work.') from error
