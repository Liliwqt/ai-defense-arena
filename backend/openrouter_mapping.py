"""Bounded structured OpenRouter IO, adapted to the existing mapping contract."""

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING
import json
import os
from time import monotonic

import httpx

from backend.question_generator import QuestionGenerationError
from backend.practice_tiers import FREE, FREE_MODEL, FREE_PROVIDER, FREE_CONTEXT_TOKENS, validate_tier
from backend.provider_allowance import ProviderAllowance, AllowanceError, reported_nano
from backend.openrouter_stream import ENDPOINT, payload, strict_schema, stream as open_stream

LEGACY_MODEL = 'deepseek/deepseek-v4.1-flash-1017'
MODEL = 'z-ai/glm-5.3-flash'


def mapping_timeout_seconds():
    """Operator transport limit; applies to retained preparations on their next attempt."""
    try:
        seconds = int(os.getenv('OPENROUTER_MAPPING_TIMEOUT_SECONDS', '300'))
        if not 30 <= seconds <= 600:
            raise ValueError
        return seconds
    except ValueError:
        raise QuestionGenerationError('Check OPENROUTER_MAPPING_TIMEOUT_SECONDS on the server (30–600 seconds).') from None


@dataclass(frozen=True)
class MappingPolicy:
    max_output_tokens: int = 65536
    allowance_nano: int = 750_000_000
    input_nano_per_token: int = 300
    output_nano_per_token: int = 1200

    tier: str = 'standard'
    model: str = LEGACY_MODEL
    reasoning_tokens: int | None = None
    request_limit: int | None = None
    context_tokens: int | None = None
    provider_only: list[str] | None = None
    # Retained policies without this field used high reasoning.
    reasoning_effort: str = 'high'

    @classmethod
    def configured(cls, tier='standard'):
        validate_tier(tier)
        if tier == FREE:
            return cls(max_output_tokens=16384, tier=FREE, model=FREE_MODEL,
                       reasoning_tokens=4096, request_limit=3,
                       context_tokens=FREE_CONTEXT_TOKENS, provider_only=[FREE_PROVIDER])
        try:
            output = int(os.getenv('OPENROUTER_MAPPING_MAX_OUTPUT_TOKENS', '65536'))
            ceiling = Decimal(os.getenv('OPENROUTER_PREPARATION_USD', '0.75'))
            effort = os.getenv('OPENROUTER_MAPPING_REASONING_EFFORT', 'low')
            if effort not in {'low', 'high'}:
                raise QuestionGenerationError('Check OPENROUTER_MAPPING_REASONING_EFFORT on the server (low or high).')
            model = os.getenv('OPENROUTER_MAPPING_MODEL', MODEL)
            if model not in {MODEL, LEGACY_MODEL}:
                raise QuestionGenerationError('Check OPENROUTER_MAPPING_MODEL on the server (z-ai/glm-5.3-flash or deepseek/deepseek-v4.1-flash-1017).')
            if not 1024 <= output <= 131072 or not ceiling.is_finite() or not Decimal('0') < ceiling <= 10:
                raise ValueError
            return cls(output, int((ceiling * 1_000_000_000).to_integral_value(rounding=ROUND_CEILING)), model=model, reasoning_effort=effort)
        except (ValueError, InvalidOperation):
            raise QuestionGenerationError('Check OPENROUTER_MAPPING_MAX_OUTPUT_TOKENS and OPENROUTER_PREPARATION_USD on the server.') from None


class MappingClient:
    @property
    def mapping_reasoning(self):
        if self.policy.reasoning_tokens is not None:
            return {'max_tokens': self.policy.reasoning_tokens}
        return {'effort': self.policy.reasoning_effort}

    def __init__(self, scope: str, owner: str, api_key=None, *, stopped=lambda: False, tier='standard'):
        key = (api_key if api_key is not None else os.getenv('OPENROUTER_API_KEY', '')).strip()
        if not key or any(char.isspace() for char in key):
            raise QuestionGenerationError('Set a clean OPENROUTER_API_KEY on the server to map the paper.')
        self.api_key = key
        self.allowance = ProviderAllowance(scope, owner)
        try:
            stored = self.allowance.policy()
            if stored is None:
                configured = MappingPolicy.configured(tier)
                stored = self.allowance.establish(configured.allowance_nano, asdict(configured))
            self.policy = MappingPolicy(**stored)
            if self.policy.tier != tier:
                raise QuestionGenerationError("The preparation tier is fixed. Create a new room to change it.")
        except AllowanceError as error:
            raise QuestionGenerationError(str(error)) from None
        self.stopped = stopped
        self.responses = self

    def parse(self, **request):
        with self.stream(**request) as stream:
            for _ in stream:
                pass
            return stream.get_final_response()

    @contextmanager
    def stream(self, *, input, text_format, **unused):
        timeout_seconds = mapping_timeout_seconds()
        deadline = monotonic() + timeout_seconds

        def current():
            if self.stopped():
                raise QuestionGenerationError('OpenRouter mapping was cancelled.')
            if monotonic() >= deadline:
                raise QuestionGenerationError(f'OpenRouter mapping exceeded its {timeout_seconds}-second time limit. Retry mapping when ready.')

        current()
        schema = strict_schema(text_format.model_json_schema())
        body = payload(self.policy.model, input, text_format, reasoning={**self.mapping_reasoning, 'exclude': True},
                       max_tokens=self.policy.max_output_tokens, free=self.policy.tier == FREE,
                       provider_only=self.policy.provider_only)
        # Byte fallback is a conservative token bound; include schema/message
        # serialization and a fixed allowance for provider framing, never truncate.
        input_bound = len(json.dumps({'messages': input, 'schema': schema}, ensure_ascii=False).encode()) + 8192
        context = self.policy.context_tokens or (1_000_000 if self.policy.tier == FREE else 1_048_576)
        if input_bound + self.policy.max_output_tokens > context:
            raise QuestionGenerationError('The accepted material exceeds the bounded OpenRouter mapping context. Reduce the material; it was not truncated.')
        bound = input_bound * self.policy.input_nano_per_token + self.policy.max_output_tokens * self.policy.output_nano_per_token
        try:
            identity = self.allowance.reserve(bound)
        except AllowanceError as error:
            raise QuestionGenerationError(str(error)) from None
        try:
            current()
            with httpx.Client(timeout=httpx.Timeout(30, connect=10, read=30), follow_redirects=False) as client:
                with open_stream(client, api_key=self.api_key, body=body, schema=text_format,
                        current=current, on_usage=lambda usage: self._settle_usage(identity, usage)) as stream:
                    yield stream
        except httpx.HTTPError:
            raise QuestionGenerationError('OpenRouter mapping connection failed. Retry when the service is available.') from None

    def _settle_usage(self, identity, usage):
        # Settle every valid receipt so a later conflicting receipt cannot
        # overwrite earlier evidence. Missing evidence keeps the full bound.
        value = reported_nano(usage)
        if value is None:
            return
        try:
            self.allowance.settle(identity, value)
        except AllowanceError as error:
            raise QuestionGenerationError(str(error)) from None

