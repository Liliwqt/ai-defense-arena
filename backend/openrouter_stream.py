"""Shared bounded OpenRouter chat-completions transport.

One place owns the endpoint, strict-schema preparation, request payload and
streamed structured-output parsing so paper mapping and funded defense
questions cannot drift into different provider contracts.
"""

from contextlib import contextmanager
import json
from types import SimpleNamespace

import httpx
from pydantic import ValidationError

from backend.question_generator import InvalidQuestionResponse, QuestionGenerationError

ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'
MAX_RESPONSE_CHARS = 2_000_000


class TransientProviderError(QuestionGenerationError):
    """A temporary provider failure that one bounded fresh request may recover."""

    retryable = True


class ProviderConnectionError(TransientProviderError):
    """The provider could not be reached; a fresh request may recover."""


class ProviderStatusError(TransientProviderError):
    """The provider rejected one request; only server failures are retryable."""

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = status_code >= 500


def provider_stream_error(error):
    """Classify a provider envelope without exposing its upstream message.

    Headers may already be HTTP200 when a provider rejects the request. Unknown
    errors require operator/manual recovery rather than spending on a retry as
    though the model merely produced malformed JSON.
    """
    if isinstance(error, dict):
        code = error.get('code')
        metadata = error.get('metadata')
        error_type = metadata.get('error_type') if isinstance(metadata, dict) else None
        if error_type == 'rate_limit_exceeded':
            code = 429
        if type(code) is int and 400 <= code <= 599:
            return ProviderStatusError(code, f'OpenRouter request failed (HTTP {code}). Check server configuration or retry later.')
        if code == 'server_error' or error_type == 'server_error':
            return ProviderStatusError(500, 'OpenRouter server error. Retry when the service is available.')
    return QuestionGenerationError('OpenRouter reported a provider error. Check server configuration or retry later.')


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


def payload(model, messages, schema, *, reasoning, max_tokens):
    """One guarded request body; routes without the exact contract are excluded."""
    return {'model': model, 'messages': messages, 'reasoning': reasoning,
        'max_tokens': max_tokens, 'stream': True,
        'stream_options': {'include_usage': True},
        'response_format': {'type': 'json_schema', 'json_schema': {
            'name': schema.__name__, 'strict': True, 'schema': strict_schema(schema.model_json_schema())}},
        'provider': {'allow_fallbacks': False, 'require_parameters': True,
            'data_collection': 'deny', 'max_price': {'prompt': .30, 'completion': 1.20, 'request': 0}}}


class StructuredStream:
    """SSE parse for one dispatched structured request."""

    def __init__(self, response, schema, current, on_usage):
        self.response, self.schema = response, schema
        self.current, self.on_usage = current, on_usage
        self.text = ''
        self.finished = False

    def __iter__(self):
        for line in self.response.iter_lines():
            self.current()
            if not line.startswith('data:'):
                continue
            raw = line[5:].strip()
            if raw == '[DONE]':
                break
            if len(raw) > MAX_RESPONSE_CHARS:
                raise QuestionGenerationError('OpenRouter exceeded the response limit.')
            try:
                event = json.loads(raw)
                if 'error' in event:
                    raise provider_stream_error(event['error'])
                if event.get('usage') is not None:
                    self.on_usage(event['usage'])
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
                        if not isinstance(content, str) or len(self.text) + len(content) > MAX_RESPONSE_CHARS:
                            raise ValueError
                        self.text += content
                        yield SimpleNamespace(type='response.output_text.delta', output_index=0,
                                              content_index=0, delta=content)
            except (ValueError, TypeError, AttributeError):
                raise InvalidQuestionResponse('OpenRouter returned an invalid or incomplete structured response. Retry.') from None

    def get_final_response(self):
        if not self.finished:
            raise InvalidQuestionResponse('OpenRouter ended before completing the structured response. Retry.')
        try:
            return SimpleNamespace(output_parsed=self.schema.model_validate_json(self.text))
        except ValidationError:
            raise InvalidQuestionResponse('OpenRouter returned an invalid structured response. Retry.') from None


@contextmanager
def stream(client, *, api_key, body, schema, current, on_usage):
    """Yield one parsed stream; transport failures never fall back elsewhere."""
    try:
        with client.stream('POST', ENDPOINT, json=body, headers={'Authorization': 'Bearer ' + api_key}) as response:
            if response.status_code != 200:
                raise ProviderStatusError(response.status_code, f'OpenRouter request failed (HTTP {response.status_code}). Check server configuration or retry later.')
            yield StructuredStream(response, schema, current, on_usage)
    except httpx.HTTPError:
        raise ProviderConnectionError('OpenRouter connection failed. Retry when the service is available.') from None
