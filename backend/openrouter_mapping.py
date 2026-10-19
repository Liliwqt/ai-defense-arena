"""Bounded structured OpenRouter IO, adapted to the existing mapping contract."""

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING
import json
import os
from time import monotonic
from types import SimpleNamespace

import httpx
from pydantic import ValidationError

from backend.question_generator import QuestionGenerationError
from backend.provider_allowance import ProviderAllowance, AllowanceError

MODEL = 'deepseek/deepseek-v4.1-flash-1017'
ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'


@dataclass(frozen=True)
class MappingPolicy:
    max_output_tokens: int = 65536
    allowance_nano: int = 750_000_000
    input_nano_per_token: int = 300
    output_nano_per_token: int = 1200

    @classmethod
    def configured(cls):
        try:
            output = int(os.getenv('OPENROUTER_MAPPING_MAX_OUTPUT_TOKENS', '65536'))
            ceiling = Decimal(os.getenv('OPENROUTER_PREPARATION_USD', '0.75'))
            if not 1024 <= output <= 131072 or not ceiling.is_finite() or not Decimal('0') < ceiling <= 10:
                raise ValueError
            return cls(output, int((ceiling * 1_000_000_000).to_integral_value(rounding=ROUND_CEILING)))
        except (ValueError, InvalidOperation):
            raise QuestionGenerationError('Check OPENROUTER_MAPPING_MAX_OUTPUT_TOKENS and OPENROUTER_PREPARATION_USD on the server.') from None


def strict_schema(schema):
    """Keep source validation local while requiring supported structured output."""
    if isinstance(schema, dict):
        schema = {key: strict_schema(value) for key, value in schema.items()}
        if schema.get('type') == 'object':
            schema['additionalProperties'] = False
            schema['required'] = list(schema.get('properties', {}))
    elif isinstance(schema, list):
        schema = [strict_schema(value) for value in schema]
    return schema


class MappingClient:
    mapping_reasoning = {'effort': 'high'}

    def __init__(self, scope: str, owner: str, api_key=None, *, stopped=lambda: False):
        key = (api_key if api_key is not None else os.getenv('OPENROUTER_API_KEY', '')).strip()
        if not key or any(char.isspace() for char in key):
            raise QuestionGenerationError('Set a clean OPENROUTER_API_KEY on the server to map the paper.')
        self.api_key = key
        self.allowance = ProviderAllowance(scope, owner)
        try:
            stored = self.allowance.policy()
            if stored is None:
                configured = MappingPolicy.configured()
                stored = self.allowance.establish(configured.allowance_nano, asdict(configured))
            self.policy = MappingPolicy(**stored)
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
        deadline = monotonic() + 90

        def current():
            if self.stopped() or monotonic() >= deadline:
                raise QuestionGenerationError('OpenRouter mapping was cancelled or timed out. Retry when ready.')

        current()
        schema = strict_schema(text_format.model_json_schema())
        payload = {'model': MODEL, 'messages': input, 'reasoning': {'effort': 'high', 'exclude': True},
            'max_tokens': self.policy.max_output_tokens, 'stream': True,
            'stream_options': {'include_usage': True},
            'response_format': {'type': 'json_schema', 'json_schema': {
                'name': text_format.__name__, 'strict': True, 'schema': schema}},
            'provider': {'allow_fallbacks': False, 'require_parameters': True,
                'data_collection': 'deny', 'max_price': {'prompt': .30, 'completion': 1.20, 'request': 0}}}
        # Byte fallback is a conservative token bound; include schema/message
        # serialization and a fixed allowance for provider framing, never truncate.
        input_bound = len(json.dumps({'messages': input, 'schema': schema}, ensure_ascii=False).encode()) + 8192
        if input_bound + self.policy.max_output_tokens > 1_048_576:
            raise QuestionGenerationError('The accepted material exceeds the bounded OpenRouter mapping context. Reduce the material; it was not truncated.')
        bound = input_bound * self.policy.input_nano_per_token + self.policy.max_output_tokens * self.policy.output_nano_per_token
        try:
            identity = self.allowance.reserve(bound)
        except AllowanceError as error:
            raise QuestionGenerationError(str(error)) from None
        try:
            current()
            with httpx.Client(timeout=httpx.Timeout(90, read=15), follow_redirects=False) as client:
                with client.stream('POST', ENDPOINT, json=payload,
                        headers={'Authorization': 'Bearer ' + self.api_key}) as response:
                    if response.status_code != 200:
                        raise QuestionGenerationError(f'OpenRouter mapping failed (HTTP {response.status_code}). Check server configuration or retry later.')
                    stream = MapStream(response, text_format, current,
                        lambda usage: self._settle_usage(identity, usage))
                    yield stream
        except httpx.HTTPError:
            raise QuestionGenerationError('OpenRouter mapping connection failed. Retry when the service is available.') from None

    def _settle_usage(self, identity, usage):
        # Settle every valid receipt so a later conflicting receipt cannot
        # overwrite earlier evidence. Missing evidence keeps the full bound.
        cost = usage.get('cost') if isinstance(usage, dict) else None
        try:
            value = Decimal(str(cost))
            if value.is_finite() and 0 <= value <= 1_000_000:
                self.allowance.settle(identity, int((value * 1_000_000_000).to_integral_value(rounding=ROUND_CEILING)))
        except InvalidOperation:
            pass
        except AllowanceError as error:
            raise QuestionGenerationError(str(error)) from None


class MapStream:
    def __init__(self, response, schema, current, settle_usage):
        self.response, self.schema = response, schema
        self.current = current
        self.text = ''
        self.finished = False
        self.settle_usage = settle_usage

    def __iter__(self):
        for line in self.response.iter_lines():
            self.current()
            if not line.startswith('data:'):
                continue
            raw = line[5:].strip()
            if raw == '[DONE]':
                break
            if len(raw) > 2_000_000:
                raise QuestionGenerationError('OpenRouter mapping exceeded the response limit.')
            try:
                event = json.loads(raw)
                if 'error' in event:
                    raise ValueError
                if event.get('usage') is not None:
                    self.settle_usage(event['usage'])
                for choice in event.get('choices', []):
                    if choice.get('index') != 0:
                        raise ValueError
                    finish = choice.get('finish_reason')
                    if finish is not None:
                        if finish != 'stop':
                            raise ValueError
                        self.finished = True
                    content = choice.get('delta', {}).get('content')
                    if content:
                        if not isinstance(content, str) or len(self.text) + len(content) > 2_000_000:
                            raise ValueError
                        self.text += content
                        yield SimpleNamespace(type='response.output_text.delta', output_index=0,
                                              content_index=0, delta=content)
            except (ValueError, TypeError, AttributeError):
                raise QuestionGenerationError('OpenRouter returned an invalid or incomplete research map. Retry preparing the defense.') from None

    def get_final_response(self):
        if not self.finished:
            raise QuestionGenerationError('OpenRouter mapping ended before completion. Retry preparing the defense.')
        try:
            return SimpleNamespace(output_parsed=self.schema.model_validate_json(self.text))
        except ValidationError:
            raise QuestionGenerationError('OpenRouter returned an invalid structured map. Retry preparing the defense.') from None
