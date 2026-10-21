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
_FUNDING_MARKERS = (
    'insufficient_quota',
    'insufficient credit',
    'insufficient_credits',
    'not enough credit',
    'requires more credits',
    'credit balance',
    'exceeded your current quota',
    'billing_hard_limit_reached',
)


def funding_exhausted(payload=None, message: str = '') -> bool:
    """Recognize exhausted funds in provider-controlled error metadata."""
    values = [message]
    if isinstance(payload, dict):
        values.extend(payload.get(key) for key in ('message', 'code', 'type'))
        metadata = payload.get('metadata')
        if isinstance(metadata, dict):
            values.extend(metadata.get(key) for key in (
                'message', 'code', 'type', 'error_type', 'provider_code'))
    elif payload is not None:
        values.append(str(payload))
    text = ' '.join(value for value in values if isinstance(value, str)).lower()
    return any(marker in text for marker in _FUNDING_MARKERS)


class TransientProviderError(QuestionGenerationError):
    """A temporary provider failure that one bounded fresh request may recover."""

    retryable = True


class ProviderConnectionError(TransientProviderError):
    """The provider could not be reached; a fresh request may recover."""


class ProviderStatusError(TransientProviderError):
    """The provider rejected one request; server failures and bounded 429s are retryable."""

    def __init__(self, status_code: int, message: str, *,
                 retry_after_seconds: int | None = None, manual_only: bool = False):
        super().__init__(message)
        if (isinstance(retry_after_seconds, bool) or not isinstance(retry_after_seconds, int)
                or not 0 <= retry_after_seconds <= 86_400):
            retry_after_seconds = None
        self.status_code = status_code
        self.retry_after_seconds = retry_after_seconds
        self.manual_only = manual_only or (status_code == 429 and funding_exhausted(message=message))
        self.retryable = status_code >= 500 or (
            status_code == 429 and not self.manual_only and retry_after_seconds is not None)


def retry_after_seconds(value) -> int | None:
    """Accept only a whole, non-negative delta-seconds value from the provider."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if 0 <= value <= 86_400 else None
    if isinstance(value, str):
        text = value.strip()
        if text.isdigit():
            seconds = int(text)
            return seconds if seconds <= 86_400 else None
    return None


def header_retry_after(headers) -> int | None:
    try:
        return retry_after_seconds(headers.get('retry-after'))
    except (AttributeError, TypeError):
        return None


def envelope_retry_after(error) -> int | None:
    if not isinstance(error, dict):
        return None
    metadata = error.get('metadata')
    for value in (error.get('retry_after'), error.get('retry_after_seconds'),
                  metadata.get('retry_after') if isinstance(metadata, dict) else None,
                  metadata.get('retry_after_seconds') if isinstance(metadata, dict) else None):
        seconds = retry_after_seconds(value)
        if seconds is not None:
            return seconds
    return None


def status_error(status, error=None, retry_after: int | None = None):
    """Classify known routing reasons without copying provider-controlled text."""
    retry_after = retry_after_seconds(retry_after)
    if status == 429:
        message = error.get('message', '') if isinstance(error, dict) else ''
        message = message.lower() if isinstance(message, str) else ''
        if message.startswith('rate limit exceeded: free-models-per-day'):
            return ProviderStatusError(status, 'OpenRouter’s daily free-model request allowance is exhausted (HTTP 429). Wait for the next UTC day or ask the operator to check the account’s free-model allowance. Retrying now will not reset it.',
                                       retry_after_seconds=retry_after, manual_only=True)
        if 'per-day' in message or 'daily' in message:
            return ProviderStatusError(status, 'OpenRouter’s daily request allowance is exhausted (HTTP 429). Wait for the next UTC day or ask the operator to check the account’s allowance. Retrying now will not reset it.',
                                       retry_after_seconds=retry_after, manual_only=True)
        if funding_exhausted(error, message):
            return ProviderStatusError(status, 'OpenRouter cannot fund this request (HTTP 429). Check the account’s credits or billing settings, or contact the operator. Retrying now will not reset it.',
                                       retry_after_seconds=retry_after, manual_only=True)
        if message.startswith('rate limit exceeded: free-models-per-min'):
            return ProviderStatusError(status, 'OpenRouter’s per-minute free-model request limit was reached (HTTP 429). Wait at least a minute before retrying. Repeated retries also consume free requests.',
                                       retry_after_seconds=retry_after)
        return ProviderStatusError(status, 'OpenRouter or the selected provider reached a rate or capacity limit (HTTP 429). Wait before retrying. If it persists, ask the operator to check OpenRouter Activity and the account’s free-model allowance.',
                                   retry_after_seconds=retry_after)
    if status == 404:
        message = error.get('message', '') if isinstance(error, dict) else ''
        if isinstance(message, str) and message.lower().startswith('no endpoints found matching your data policy'):
            return ProviderStatusError(status, 'OpenRouter has no endpoint matching the app/account privacy settings (HTTP 404). The operator needs to configure a compatible model and provider.')
        return ProviderStatusError(status, 'OpenRouter found no compatible endpoint for the configured model and request (HTTP 404). Check model/provider availability and supported parameters.')
    return ProviderStatusError(status, f'OpenRouter request failed (HTTP {status}). Check server configuration or retry later.',
                               retry_after_seconds=retry_after)


def http_status_error(response, current):
    """Bound error reads; malformed/oversized bodies retain the HTTP verdict."""
    retry_after = header_retry_after(response.headers)
    data = bytearray()
    try:
        for chunk in response.iter_bytes():
            current()
            if len(data) + len(chunk) > MAX_ERROR_BYTES:
                return status_error(response.status_code, retry_after=retry_after)
            data.extend(chunk)
        document = json.loads(data)
        error = document.get('error') if isinstance(document, dict) else None
        return status_error(response.status_code, error,
                            retry_after=retry_after if retry_after is not None else envelope_retry_after(error))
    except (ValueError, UnicodeError, RecursionError, httpx.HTTPError):
        return status_error(response.status_code, retry_after=retry_after)


def provider_stream_error(error, *, retry_after: int | None = None):
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
        retry_after = retry_after if retry_after is not None else envelope_retry_after(error)
        if type(code) is int and 400 <= code <= 599:
            return status_error(code, error, retry_after=retry_after)
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
                    raise provider_stream_error(event['error'], retry_after=header_retry_after(self.response.headers))
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
