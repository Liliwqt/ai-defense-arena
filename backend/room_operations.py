"""Authoritative room operation identity and content-free timing records."""

from contextvars import ContextVar
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_CEILING
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import secrets
from pathlib import Path
from threading import Lock

_LOGGER = logging.getLogger("defense.operation_timing")
_SAFE_USAGE = ("input_tokens", "output_tokens", "reasoning_tokens", "cost_nano", "model", "provider",
               "lookup_bytes", "lookup_requests", "lookup_duration_ms")
_OPERATION = ContextVar("operation_timing_operation", default=None)
_USAGE_LOCK = Lock()
_ACTIVE_OPERATIONS: set[str] = set()
_SUPPLIED_USAGE: dict[str, dict] = {}


def _configure_logger() -> None:
    if _LOGGER.handlers:
        return
    handler = None
    path = os.environ.get("OPERATION_TIMING_LOG")
    if path:
        try:
            target = Path(path).expanduser()
            target.resolve().parent.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(target, maxBytes=2_000_000, backupCount=3)
        except OSError:
            handler = None
    if handler is None:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    _LOGGER.addHandler(handler)
    _LOGGER.setLevel(logging.INFO)
    _LOGGER.propagate = False


_configure_logger()


@dataclass
class RoomOperation:
    id: str
    kind: str
    stage: str
    started_at_ms: int
    stage_started_at_ms: int
    attempt: int = 1
    retrying: bool = False
    # Public IDs are room-local and remain compatible with existing snapshots.
    # An opaque lifetime identity isolates receipts, including late callbacks.
    usage_key: str = field(default_factory=lambda: secrets.token_hex(24), repr=False)
    stage_finished: bool = False
    window_deadline_ms: int | None = None
    retry_at_ms: int | None = None

    def snapshot(self) -> dict:
        result = {
            "id": self.id,
            "kind": self.kind,
            "stage": self.stage,
            "started_at_ms": self.started_at_ms,
            "attempt": self.attempt,
            "retrying": self.retrying,
        }
        if self.window_deadline_ms is not None:
            result["window_deadline_ms"] = self.window_deadline_ms
        if self.retry_at_ms is not None:
            result["retry_at_ms"] = self.retry_at_ms
        return result


class TimingSink:
    def emit(self, record: dict) -> None:
        raise NotImplementedError


class _LogSink(TimingSink):
    def emit(self, record: dict) -> None:
        _LOGGER.info("operation_timing %s", json.dumps(record, sort_keys=True, separators=(",", ":")))


_sink: TimingSink = _LogSink()


def install_timing_sink(sink: TimingSink) -> None:
    global _sink
    _sink = sink


def reset_timing_sink() -> None:
    global _sink
    _sink = _LogSink()


def _number(value) -> int | float | None:
    if type(value) in (int, float) and value >= 0:
        return value
    return None


def _nano(value) -> int | None:
    try:
        amount = Decimal(str(value))
        if amount.is_finite() and 0 <= amount <= 1_000_000:
            return int((amount * 1_000_000_000).to_integral_value(rounding=ROUND_CEILING))
    except (InvalidOperation, ValueError):
        pass
    return None


def _supplied_fields(usage: dict, *, model: str | None = None) -> dict:
    if not isinstance(usage, dict):
        return {}
    details = usage.get("completion_tokens_details")
    details = details if isinstance(details, dict) else {}
    fields = {
        "input_tokens": _number(usage.get("input_tokens", usage.get("prompt_tokens"))),
        "output_tokens": _number(usage.get("output_tokens", usage.get("completion_tokens"))),
        "reasoning_tokens": _number(usage.get("reasoning_tokens", details.get("reasoning_tokens"))),
        "cost_nano": _nano(usage.get("cost")),
        "lookup_bytes": _number(usage.get("lookup_bytes")),
        "lookup_requests": _number(usage.get("lookup_requests")),
        "lookup_duration_ms": _number(usage.get("lookup_duration_ms")),
    }
    if model:
        fields["model"] = model
    provider = usage.get("provider")
    if isinstance(provider, str) and provider:
        fields["provider"] = provider
    return {key: value for key, value in fields.items() if value is not None}


def bind_operation(operation_id: str) -> None:
    with _USAGE_LOCK:
        _ACTIVE_OPERATIONS.add(operation_id)
        _SUPPLIED_USAGE.pop(operation_id, None)
    _OPERATION.set(operation_id)


def release_operation(operation_id: str) -> None:
    with _USAGE_LOCK:
        _ACTIVE_OPERATIONS.discard(operation_id)
        _SUPPLIED_USAGE.pop(operation_id, None)
    if _OPERATION.get() == operation_id:
        _OPERATION.set(None)


def record_supplied_usage(usage: dict, *, model: str | None = None) -> None:
    operation_id = _OPERATION.get()
    if not operation_id:
        return
    fields = _supplied_fields(usage, model=model)
    if not fields:
        return
    with _USAGE_LOCK:
        if operation_id not in _ACTIVE_OPERATIONS:
            return
        supplied = _SUPPLIED_USAGE.setdefault(operation_id, {})
        for key, value in fields.items():
            if key in {"input_tokens", "output_tokens", "reasoning_tokens", "cost_nano",
                       "lookup_bytes", "lookup_requests", "lookup_duration_ms"}:
                supplied[key] = supplied.get(key, 0) + value
            else:
                supplied[key] = value


def take_supplied_usage(operation_id: str, usage: dict | None = None) -> dict:
    with _USAGE_LOCK:
        supplied = _SUPPLIED_USAGE.pop(operation_id, {})
        _ACTIVE_OPERATIONS.discard(operation_id)
    if _OPERATION.get() == operation_id:
        _OPERATION.set(None)
    return {**supplied, **(usage or {})}


def _safe_usage(usage: dict | None) -> dict:
    if not usage:
        return {}
    return {
        key: value for key, value in usage.items()
        if key in _SAFE_USAGE and type(value) in (int, float, str) and value is not None
    }


def _emit(record: dict) -> None:
    try:
        _sink.emit(record)
    except Exception:
        _LOGGER.warning("operation timing sink failed", exc_info=True)


def record_stage(operation: RoomOperation, *, ended_at_ms: int, outcome: str,
                 usage: dict | None = None, failure_class: str | None = None) -> None:
    _emit({
        "event": "stage",
        "operation_id": operation.id,
        "measurement_id": operation.usage_key,
        "kind": operation.kind,
        "stage": operation.stage,
        "attempt": operation.attempt,
        "retrying": operation.retrying,
        "started_at_ms": operation.stage_started_at_ms,
        "ended_at_ms": ended_at_ms,
        "duration_ms": max(0, ended_at_ms - operation.stage_started_at_ms),
        "outcome": outcome,
        **({"failure_class": failure_class} if failure_class else {}),
        **_safe_usage(usage),
    })


def record_total(operation: RoomOperation, *, ended_at_ms: int, outcome: str,
                 usage: dict | None = None, failure_class: str | None = None) -> None:
    _emit({
        "event": "total",
        "operation_id": operation.id,
        "measurement_id": operation.usage_key,
        "kind": operation.kind,
        "stage": operation.stage,
        "attempts": operation.attempt,
        "retrying": operation.retrying,
        "started_at_ms": operation.started_at_ms,
        "ended_at_ms": ended_at_ms,
        "duration_ms": max(0, ended_at_ms - operation.started_at_ms),
        "outcome": outcome,
        **({"failure_class": failure_class} if failure_class else {}),
        **_safe_usage(usage),
    })
