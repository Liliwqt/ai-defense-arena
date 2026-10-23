"""Opt-in synthetic benchmark HTTP observer and persistent campaign spending cap."""
from copy import deepcopy
import json
from threading import Lock
from time import monotonic

import httpx

from backend.openrouter_questions import FRAMING_BYTES
from backend.provider_allowance import ProviderAllowance, reported_nano
from backend.openrouter_stream import MAX_ERROR_BYTES, header_retry_after, envelope_retry_after
from tests.operation_timing_harness import PROVIDER_USAGE_FIELDS as USAGE

HTTPClient = httpx.Client
URL = 'https://openrouter.ai/api/v1/chat/completions'


class CampaignObserver:
    def __init__(self, identity, ceiling, policy, *, transport_factory=None, provider_routes=None):
        self._provider_routes = deepcopy(provider_routes or {})
        self.allowance = ProviderAllowance('benchmark:'+identity, 'synthetic-benchmark')
        saved = {'ceiling': ceiling, 'purpose': 'synthetic-reviewer-benchmark'}
        if self._provider_routes:
            saved['provider_routes'] = self._provider_routes
        stored = self.allowance.establish(ceiling, saved)
        if stored['ceiling'] != ceiling:
            raise ValueError('A campaign cannot change its approved ceiling.')
        if stored.get('provider_routes', {}) != self._provider_routes:
            raise ValueError('A campaign cannot change its captured provider routes.')
        self.policy = policy
        self.transport_factory = transport_factory or (lambda: httpx.HTTPTransport(retries=0))
        self.context = {}
        self.records = []
        self._lock = Lock()
        self._active = {}

    def client(self, *args, **kwargs):
        if args or 'transport' in kwargs:
            raise ValueError('The benchmark requires its observed transport.')
        return HTTPClient(transport=_ObservedTransport(self, self.transport_factory()), **kwargs)

    def append(self, record):
        with self._lock:
            self.records.append(record)
            self._active.pop(record['request_id'], None)

    def request_started(self, record, started):
        with self._lock:
            self._active[record['request_id']] = (deepcopy(record), started)

    def snapshot(self):
        with self._lock:
            active = [{**record, 'duration_ms': round((monotonic()-started)*1000), 'outcome': 'in_flight'}
                      for record, started in self._active.values()]
            return deepcopy(self.records)+active, len(active)


class _ObservedTransport(httpx.BaseTransport):
    def __init__(self, observer, transport):
        self.observer, self.transport = observer, transport
        self.context = deepcopy(observer.context)
        self.routes = deepcopy(observer._provider_routes.get(self.context.get('condition'), {}))

    def handle_request(self, request):
        if str(request.url) != URL:
            raise ValueError('Only the OpenRouter interactive endpoint is allowed.')
        body = json.loads(request.content)
        provider = body['provider']
        if (provider.get('allow_fallbacks') is not False or provider.get('require_parameters') is not True
                or provider.get('data_collection') != 'deny'
                or provider.get('max_price') != {'prompt': .30, 'completion': 1.20, 'request': 0}):
            raise ValueError('The benchmark cannot relax routing/privacy/price controls.')
        route = self.routes.get(body['model'])
        if route:
            selector = {'only': [route]} if isinstance(route, str) else route
            if (not isinstance(selector, dict) or set(selector) - {'only', 'ignore'}
                    or not selector.get('only') or any(
                        not isinstance(values, list) or not values or any(
                            not isinstance(value, str) or not value.strip() for value in values)
                        for values in selector.values())):
                raise ValueError('A benchmark route must contain explicit only/ignore provider lists.')
            for key, values in selector.items():
                if provider.get(key) not in (None, values):
                    raise ValueError('A benchmark route cannot override a saved provider restriction.')
                provider[key] = list(values)
            # Rebuild the request so Content-Length reflects the routing selector.
            # Only this model's provider restriction changes; preserve auth privately.
            request = httpx.Request(request.method, request.url,
                headers=[(key, value) for key, value in request.headers.multi_items()
                         if key.lower() != 'content-length'],
                content=json.dumps(body).encode(), extensions=request.extensions)
        bound = self.observer.policy.stage_bound(
            len(json.dumps({'messages': body['messages'], 'schema': body['response_format']}, ensure_ascii=False).encode())+FRAMING_BYTES,
            body['max_tokens'])
        reservation = self.observer.allowance.reserve(bound)
        record = {**self.context, 'event': 'stage', 'kind': 'provider_request',
            'stage': body['response_format']['json_schema']['name'], 'model': body['model'],
            'reasoning': body['reasoning'], 'max_tokens': body['max_tokens'],
            **({'requested_provider': route} if route else {}),
            'reserved_nano': bound, 'request_id': reservation}
        started = monotonic()
        self.observer.request_started(record, started)
        try:
            response = self.transport.handle_request(request)
        except Exception as error:
            self.observer.append({**record, 'duration_ms': round((monotonic()-started)*1000),
                                  'outcome': 'failed', 'failure_class': type(error).__name__})
            raise
        return httpx.Response(response.status_code, headers=response.headers,
            stream=_ObservedStream(response.stream, self.observer, record, reservation, started,
                                   response.status_code, response.headers),
            extensions=response.extensions)

    def close(self):
        self.transport.close()


class _ObservedStream(httpx.SyncByteStream):
    def __init__(self, delegate, observer, record, reservation, started, status, headers):
        self.delegate, self.observer, self.record = delegate, observer, record
        self.reservation, self.started, self.status = reservation, started, status
        self.pending = b''
        self.receipt = None
        self.conflicting_usage = False
        self.closed = False
        self.record['http_status'] = status
        retry = header_retry_after(headers)
        if retry is not None:
            self.record['retry_after_seconds'] = retry
        self.error_body = bytearray()
        self.error_oversized = False

    def __iter__(self):
        try:
            for chunk in self.delegate:
                if self.status >= 400:
                    if len(self.error_body) + len(chunk) > MAX_ERROR_BYTES:
                        self.error_body.clear()
                        self.error_oversized = True
                    elif not self.error_oversized:
                        self.error_body.extend(chunk)
                self.pending += chunk
                while b'\n' in self.pending:
                    line, self.pending = self.pending.split(b'\n', 1)
                    self._observe(line)
                if len(self.pending) > 2_000_000:
                    self.pending = b''
                yield chunk
        except Exception as error:
            self.record['failure_class'] = type(error).__name__
            raise

    def _observe(self, line):
        if not line.startswith(b'data:'):
            return
        try:
            event = json.loads(line[5:].strip())
        except (ValueError, UnicodeError):
            return
        if not isinstance(event, dict):
            return
        if isinstance(event.get('provider'), str):
            self.record['provider'] = event['provider'][:100]
        if event.get('error'):
            self.record['failure_class'] = 'ProviderStreamError'
            self._error_metadata(event['error'])
        usage = event.get('usage')
        if isinstance(usage, dict):
            details = usage.get('completion_tokens_details')
            details = details if isinstance(details, dict) else {}
            values = {'input_tokens': usage.get('prompt_tokens'), 'output_tokens': usage.get('completion_tokens'),
                'reasoning_tokens': details.get('reasoning_tokens'),
                'cost_nano': reported_nano(usage)}
            self.record.update({k: v for k, v in values.items() if type(v) is int and v >= 0})
            receipt = values['cost_nano']
            if receipt is not None:
                if self.receipt is not None and self.receipt != receipt:
                    self.conflicting_usage = True
                    self.record['failure_class'] = 'ConflictingUsage'
                self.receipt = receipt
            if self.conflicting_usage:
                self.record.pop('cost_nano', None)

    def _error_metadata(self, error):
        # Preserve only controlled diagnostic values, never message/raw/headers.
        if not isinstance(error, dict):
            return
        code = error.get('code')
        if type(code) is int and 400 <= code <= 599:
            self.record['error_code'] = code
        retry = envelope_retry_after(error)
        if retry is not None and 'retry_after_seconds' not in self.record:
            self.record['retry_after_seconds'] = retry
        metadata = error.get('metadata')
        if not isinstance(metadata, dict):
            return
        allowed = {
            'error_type': {'rate_limit_exceeded', 'provider_overloaded', 'provider_unavailable'},
            'limit_source': {'upstream_provider_shared_pool', 'upstream_provider_byok',
                'openrouter_in_flight_budget', 'openrouter_credits', 'openrouter_key_limit',
                'openrouter_guardrail_budget', 'openrouter_workspace_budget'},
            'provider_name': {'Alibaba', 'DeepInfra', 'OpenInference', 'Azure', 'Anthropic'},
        }
        for field, values in allowed.items():
            value = metadata.get(field)
            if isinstance(value, str) and value in values:
                self.record['error_provider' if field == 'provider_name' else field] = value

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            self.delegate.close()
        except Exception as error:
            self.record['failure_class'] = type(error).__name__
            raise
        finally:
            try:
                if self.status >= 400 and not self.error_oversized:
                    try:
                        document = json.loads(self.error_body)
                        self._error_metadata(document.get('error') if isinstance(document, dict) else None)
                    except (ValueError, UnicodeError, RecursionError):
                        pass
                self.error_body.clear()
                if self.receipt is not None and not self.conflicting_usage:
                    self.observer.allowance.settle(self.reservation, self.receipt)
            finally:
                self.observer.append({**self.record,
                    'duration_ms': round((monotonic()-self.started)*1000),
                    'outcome': 'failed' if self.status >= 400 or self.record.get('failure_class') else 'received',
                    **({'failure_class': 'HTTP'+str(self.status)} if self.status >= 400 else {})})
