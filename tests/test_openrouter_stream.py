"""Provider-error transport contracts; synthetic HTTP/SSE only."""

import json
import unittest

import httpx

from backend.openrouter_stream import ProviderStatusError, stream
from backend.question_generator import InvalidQuestionResponse, QuestionGenerationError


class ProviderErrorTests(unittest.TestCase):
    def test_http_privacy_rejection_has_safe_actionable_diagnostic(self):
        response = httpx.Response(404, json={'error': {'message':
            'No endpoints found matching your data policy. private upstream details'}})
        with httpx.Client(transport=httpx.MockTransport(lambda request: response)) as client:
            with self.assertRaises(ProviderStatusError) as raised:
                with stream(client, api_key='offline-key', body={}, schema=None,
                            current=lambda: None, on_usage=lambda usage: None):
                    pass
        self.assertIn('privacy', str(raised.exception))
        self.assertNotIn('private upstream details', str(raised.exception))
        self.assertFalse(raised.exception.retryable)

    def test_sse_privacy_rejection_is_sanitized_and_manual(self):
        error = self.failure({'code': 404, 'message': 'No endpoints found matching your data policy. private upstream details'})
        self.assertIn('privacy', str(error))
        self.assertFalse(error.retryable)

    def test_error_body_read_respects_request_cancellation(self):
        class ErrorBody(httpx.SyncByteStream):
            def __iter__(self):
                yield b'{'
                raise AssertionError('Cancelled request read another chunk')
        def cancelled():
            raise QuestionGenerationError('cancelled')
        response = httpx.Response(404, stream=ErrorBody())
        with httpx.Client(transport=httpx.MockTransport(lambda request: response)) as client:
            with self.assertRaisesRegex(QuestionGenerationError, 'cancelled'):
                with stream(client, api_key='offline-key', body={}, schema=None,
                            current=cancelled, on_usage=lambda usage: None):
                    pass

    def test_oversized_or_non_json_error_bodies_keep_http_status(self):
        for content in ('not JSON private upstream details', 'x' * 20000, '[ ' * 1100 + '0' + ' ]' * 1100):
            with self.subTest(size=len(content)):
                response = httpx.Response(404, text=content)
                with httpx.Client(transport=httpx.MockTransport(lambda request: response)) as client:
                    with self.assertRaises(ProviderStatusError) as raised:
                        with stream(client, api_key='offline-key', body={}, schema=None,
                                    current=lambda: None, on_usage=lambda usage: None):
                            pass
                self.assertEqual(raised.exception.status_code, 404)
                self.assertFalse(raised.exception.retryable)
                self.assertNotIn('private upstream details', str(raised.exception))

    def failure(self, error, *, http_status=200):
        response = httpx.Response(http_status, text='data: ' + json.dumps({
            'error': error, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'error'}],
        }) + '\n\n')
        with httpx.Client(transport=httpx.MockTransport(lambda request: response)) as client:
            with self.assertRaises(QuestionGenerationError) as raised:
                with stream(client, api_key='offline-key', body={}, schema=None,
                            current=lambda: None, on_usage=lambda usage: None) as events:
                    list(events)
        self.assertNotIn('private upstream details', str(raised.exception))
        return raised.exception

    def test_http_and_sse_statuses_have_the_same_recovery_policy(self):
        for status in (400, 401, 402, 403, 404, 429, 500, 502, 503, 504):
            for http_status in (status, 200):
                with self.subTest(status=status, http_status=http_status):
                    error = self.failure({'code': status, 'message': 'private upstream details'},
                                         http_status=http_status)
                    self.assertIsInstance(error, ProviderStatusError)
                    self.assertEqual(error.status_code, status)
                    self.assertEqual(error.retryable, status >= 500)

    def test_canonical_rate_limit_and_string_server_errors_are_classified(self):
        for envelope, status in (
            ({'metadata': {'error_type': 'rate_limit_exceeded'}}, 429),
            ({'code': 503, 'metadata': {'error_type': 'rate_limit_exceeded'}}, 429),
            ({'code': 'server_error'}, 500),
            ({'metadata': {'error_type': 'server_error'}}, 500),
            ({'code': 401, 'metadata': {'error_type': 'server_error'}}, 401),
        ):
            with self.subTest(envelope=envelope):
                error = self.failure(envelope)
                self.assertIsInstance(error, ProviderStatusError)
                self.assertEqual(error.status_code, status)
                self.assertEqual(error.retryable, status >= 500)

    def test_unknown_or_malformed_provider_errors_require_manual_recovery(self):
        for envelope in (None, [], 'private upstream details', {}, {'code': True},
                         {'code': 999}, {'code': 'authentication_error'},
                         {'metadata': 'private upstream details'}):
            with self.subTest(envelope=envelope):
                error = self.failure(envelope)
                self.assertNotIsInstance(error, InvalidQuestionResponse)
                self.assertFalse(getattr(error, 'retryable', False))


if __name__ == '__main__':
    unittest.main()
