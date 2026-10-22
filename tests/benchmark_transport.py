"""Opt-in synthetic benchmark HTTP observer and persistent campaign spending cap."""
from copy import deepcopy
import json
from threading import Lock
from time import monotonic

import httpx

from backend.openrouter_questions import FRAMING_BYTES
from backend.provider_allowance import ProviderAllowance, reported_nano
from tests.operation_timing_harness import PROVIDER_USAGE_FIELDS as USAGE

HTTPClient = httpx.Client
URL = 'https://openrouter.ai/api/v1/chat/completions'


class CampaignObserver:
    def __init__(self, identity, ceiling, policy, *, transport_factory=None):
        self.allowance = ProviderAllowance('benchmark:'+identity, 'synthetic-benchmark')
        stored = self.allowance.establish(ceiling, {'ceiling': ceiling, 'purpose': 'synthetic-reviewer-benchmark'})
        if stored['ceiling'] != ceiling:
            raise ValueError('A campaign cannot change its approved ceiling.')
        self.policy = policy
        self.transport_factory = transport_factory or (lambda: httpx.HTTPTransport(retries=0))
        self.context = {}
        self.records = []
        self._lock = Lock()
        self.in_flight = 0

    def client(self, *args, **kwargs):
        if args or 'transport' in kwargs:
            raise ValueError('The benchmark requires its observed transport.')
        return HTTPClient(transport=_ObservedTransport(self, self.transport_factory()), **kwargs)

    def append(self, record):
        with self._lock:
            self.records.append(record)
            self.in_flight -= 1

    def request_started(self):
        with self._lock:
            self.in_flight += 1

    def snapshot(self):
        with self._lock:
            return deepcopy(self.records), self.in_flight


class _ObservedTransport(httpx.BaseTransport):
    def __init__(self, observer, transport):
        self.observer, self.transport = observer, transport
        self.context = deepcopy(observer.context)

    def handle_request(self, request):
        if str(request.url) != URL:
            raise ValueError('Only the OpenRouter interactive endpoint is allowed.')
        body = json.loads(request.content)
        provider = body['provider']
        if (provider.get('allow_fallbacks') is not False or provider.get('require_parameters') is not True
                or provider.get('data_collection') != 'deny'
                or provider.get('max_price') != {'prompt': .30, 'completion': 1.20, 'request': 0}):
            raise ValueError('The benchmark cannot relax routing/privacy/price controls.')
        bound = self.observer.policy.stage_bound(
            len(json.dumps({'messages': body['messages'], 'schema': body['response_format']}, ensure_ascii=False).encode())+FRAMING_BYTES,
            body['max_tokens'])
        reservation = self.observer.allowance.reserve(bound)
        record = {**self.context, 'event': 'stage', 'kind': 'provider_request',
            'stage': body['response_format']['json_schema']['name'], 'model': body['model'],
            'reasoning': body['reasoning'], 'max_tokens': body['max_tokens'], 'reserved_nano': bound}
        started = monotonic()
        self.observer.request_started()
        try:
            response = self.transport.handle_request(request)
        except Exception as error:
            self.observer.append({**record, 'duration_ms': round((monotonic()-started)*1000),
                                  'outcome': 'failed', 'failure_class': type(error).__name__})
            raise
        return httpx.Response(response.status_code, headers=response.headers,
            stream=_ObservedStream(response.stream, self.observer, record, reservation, started, response.status_code),
            extensions=response.extensions)

    def close(self):
        self.transport.close()


class _ObservedStream(httpx.SyncByteStream):
    def __init__(self, delegate, observer, record, reservation, started, status):
        self.delegate, self.observer, self.record = delegate, observer, record
        self.reservation, self.started, self.status = reservation, started, status
        self.pending = b''
        self.receipt = None
        self.conflicting_usage = False
        self.closed = False

    def __iter__(self):
        try:
            for chunk in self.delegate:
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
                if self.receipt is not None and not self.conflicting_usage:
                    self.observer.allowance.settle(self.reservation, self.receipt)
            finally:
                self.observer.append({**self.record,
                    'duration_ms': round((monotonic()-self.started)*1000),
                    'outcome': 'failed' if self.status >= 400 or self.record.get('failure_class') else 'received',
                    **({'failure_class': 'HTTP'+str(self.status)} if self.status >= 400 else {})})
