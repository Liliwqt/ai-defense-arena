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
from backend.practice_tiers import RETIRED_FREE_MODEL

ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'
MAX_RESPONSE_CHARS = 2_000_000
MAX_ERROR_BYTES = 16384


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


def status_error(status, error=None):
    """Classify known routing reasons without copying provider-controlled text."""
    if status == 404:
        message = error.get('message', '') if isinstance(error, dict) else ''
        if isinstance(message, str) and message.lower().startswith('no endpoints found matching your data policy'):
            return ProviderStatusError(status, 'OpenRouter has no endpoint matching the app/account privacy settings (HTTP 404). The operator needs to configure a compatible model and provider.')
        return ProviderStatusError(status, 'OpenRouter found no compatible endpoint for the configured model and request (HTTP 404). Check model/provider availability and supported parameters.')
    return ProviderStatusError(status, f'OpenRouter request failed (HTTP {status}). Check server configuration or retry later.')


def http_status_error(response, current):
    """Bound error reads; malformed/oversized bodies retain the HTTP verdict."""
    data = bytearray()
    try:
        for chunk in response.iter_bytes():
            current()
            if len(data) + len(chunk) > MAX_ERROR_BYTES:
                return status_error(response.status_code)
            data.extend(chunk)
        document = json.loads(data)
        error = document.get('error') if isinstance(document, dict) else None
        return status_error(response.status_code, error)
    except (ValueError, UnicodeError, RecursionError, httpx.HTTPError):
        return status_error(response.status_code)


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
            return status_error(code, error)
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


def payload(model, messages, schema, *, reasoning, max_tokens, free=False, provider_only=None):
    """One guarded request body; routes without the exact contract are excluded."""
    if free and not model.endswith(':free'):
        raise QuestionGenerationError('Free practice requires a free model. No paid request was sent.')
    if free and model == RETIRED_FREE_MODEL:
        raise QuestionGenerationError('This room uses an older free model that conflicts with the app’s privacy settings. Create another room to use the updated free route; retrying this room will not change its saved model.')
    prices = {'prompt': 0, 'completion': 0, 'request': 0} if free else {'prompt': .30, 'completion': 1.20, 'request': 0}
    return {'model': model, 'messages': messages, 'reasoning': reasoning,
        'max_tokens': max_tokens, 'stream': True,
        'stream_options': {'include_usage': True},
        'response_format': {'type': 'json_schema', 'json_schema': {
            'name': schema.__name__, 'strict': True, 'schema': strict_schema(schema.model_json_schema())}},
        'provider': {'allow_fallbacks': False, 'require_parameters': True,
            'data_collection': 'deny', 'max_price': prices,
            **({'only': list(provider_only)} if provider_only else {})}}


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
                raise http_status_error(response, current)
            yield StructuredStream(response, schema, current, on_usage)
    except httpx.HTTPError:
        raise ProviderConnectionError('OpenRouter connection failed. Retry when the service is available.') from None
