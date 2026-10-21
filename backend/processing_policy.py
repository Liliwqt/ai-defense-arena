"""Versioned processing windows and one bounded transient retry."""

from dataclasses import dataclass
from typing import Literal

from openai import APIConnectionError, APIStatusError

from backend.openrouter_stream import ProviderConnectionError, ProviderStatusError
from backend.question_generator import QuestionGenerationError

LEGACY = 'legacy'
STANDARD = "bounded-standard-45s-v1"
FREE = "bounded-free-retry-v1"
STANDARD_WINDOW_MS = 45_000
DEFAULT_BACKOFF_MS = 1_000
DEFAULT_RETRY_AFTER_MAX_MS = 10_000
MAX_AUTOMATIC_RETRIES = 1


class ProcessingWindowExpired(QuestionGenerationError):
    """The current bounded attempt cannot produce a usable result in time."""


@dataclass(frozen=True)
class ProcessingPolicy:
    version: str = LEGACY
    window_ms: int | None = None
    automatic_retries: int = MAX_AUTOMATIC_RETRIES
    provider_directed_retry: bool = False
    retry_after_max_ms: int = 0
    default_backoff_ms: int = DEFAULT_BACKOFF_MS

    @classmethod
    def legacy(cls) -> "ProcessingPolicy":
        # The pre-policy question loop already retried one transient failure
        # after an accepted answer; interpretation had no automatic retry.
        return cls(automatic_retries=MAX_AUTOMATIC_RETRIES)

    @classmethod
    def standard(cls) -> "ProcessingPolicy":
        return cls(
            version=STANDARD,
            window_ms=STANDARD_WINDOW_MS,
            provider_directed_retry=True,
            retry_after_max_ms=DEFAULT_RETRY_AFTER_MAX_MS,
        )

    @classmethod
    def free(cls) -> "ProcessingPolicy":
        return cls(
            version=FREE,
            automatic_retries=MAX_AUTOMATIC_RETRIES,
            provider_directed_retry=True,
            retry_after_max_ms=DEFAULT_RETRY_AFTER_MAX_MS,
        )

    @classmethod
    def for_tier(cls, tier: str) -> "ProcessingPolicy":
        return cls.free() if tier == 'free' else cls.standard()

    def snapshot(self) -> dict:
        return {
            'version': self.version,
            'window_ms': self.window_ms,
            'automatic_retries': self.automatic_retries,
            'provider_directed_retry': self.provider_directed_retry,
            'retry_after_max_ms': self.retry_after_max_ms,
        }

    def deadline_ms(self, now_ms: int) -> int | None:
        return None if self.window_ms is None else now_ms + self.window_ms

    def remaining_ms(self, deadline_ms: int | None, now_ms: int) -> int | None:
        return None if deadline_ms is None else max(0, deadline_ms - now_ms)

    def expired(self, deadline_ms: int | None, now_ms: int) -> bool:
        return deadline_ms is not None and now_ms >= deadline_ms

    def expiry_message(self) -> str:
        if self.window_ms is None:
            return 'Processing reached its time limit. Saved work is retained; retry when ready.'
        seconds = max(1, self.window_ms // 1000)
        return (f'Processing reached the {seconds}-second limit. Saved work is retained; '
                'retry when ready.')


@dataclass(frozen=True)
class RetryDirective:
    delay_ms: int
    provider_directed: bool = False


@dataclass(frozen=True)
class RetryDecision:
    allowed: bool
    delay_ms: int = 0
    supplemental: str | None = None


def _api_status_and_retry_after(error: APIStatusError) -> tuple[int, int | None]:
    status = error.status_code
    retry_after = None
    try:
        from backend.openrouter_stream import header_retry_after
        retry_after = header_retry_after(error.response.headers)
    except (AttributeError, TypeError):
        pass
    return status, retry_after


def transient_directive(error: BaseException) -> RetryDirective | None:
    """Return a retry directive only for provider-side transient failures."""
    if isinstance(error, ProviderStatusError):
        if error.manual_only or not error.retryable:
            return None
        if error.status_code == 429:
            if error.retry_after_seconds is None:
                return None
            return RetryDirective(error.retry_after_seconds * 1000, provider_directed=True)
        return RetryDirective(DEFAULT_BACKOFF_MS)
    if isinstance(error, (ProviderConnectionError, APIConnectionError)):
        return RetryDirective(DEFAULT_BACKOFF_MS)
    if isinstance(error, APIStatusError):
        status, retry_after = _api_status_and_retry_after(error)
        if status == 429:
            if retry_after is None:
                return None
            return RetryDirective(retry_after * 1000, provider_directed=True)
        if status >= 500:
            return RetryDirective(DEFAULT_BACKOFF_MS)
    return None


def decide_retry(error: BaseException, policy: ProcessingPolicy, now_ms: int,
                 deadline_ms: int | None, attempts_remaining: int) -> RetryDecision:
    """Decide whether the same operation may spend on exactly one more try."""
    directive = transient_directive(error)
    if directive is None or policy.automatic_retries <= 0:
        return RetryDecision(False)
    if attempts_remaining <= 0:
        return RetryDecision(False)
    if directive.provider_directed:
        if not policy.provider_directed_retry:
            return RetryDecision(False)
        if directive.delay_ms > policy.retry_after_max_ms:
            return RetryDecision(
                False,
                supplemental=(f'The provider requested a {directive.delay_ms // 1000}-second wait, '
                              'beyond this room’s automatic retry limit. Use recovery to retry manually after that wait.'))
    delay_ms = directive.delay_ms if directive.provider_directed else policy.default_backoff_ms
    if deadline_ms is not None and now_ms + delay_ms >= deadline_ms:
        return RetryDecision(
            False,
            supplemental=('The automatic retry would exceed the remaining processing window. '
                          'Use recovery to retry manually.'))
    return RetryDecision(True, delay_ms=delay_ms)
