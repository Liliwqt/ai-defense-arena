"""Closed room commands and server-verified invocation identity."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, Mapping, get_args


@dataclass(frozen=True)
class SendChat:
    text: object


@dataclass(frozen=True)
class CastVote:
    seat: object


@dataclass(frozen=True)
class GenerateQuestion:
    generation_id: int
    first: bool


@dataclass(frozen=True)
class CatchUpDeadline:
    clock_id: int | None = None
    run_id: str | None = None


@dataclass(frozen=True)
class SubmitAnswer:
    turn: object
    answer: object


@dataclass(frozen=True)
class SubmitDirectAnswer:
    turn: object
    answer: object


@dataclass(frozen=True)
class SubmitProbeReply:
    turn: object
    answer: object
    probe_id: object
    direct: bool = False


@dataclass(frozen=True)
class FinishProbe:
    turn: object
    probe_id: object


@dataclass(frozen=True)
class RetryInterpretation:
    pass


@dataclass(frozen=True)
class UsePendingAnswer:
    pass


@dataclass(frozen=True)
class InterpretSubmission:
    interpretation_id: int


SubmissionCommand = SubmitAnswer | SubmitDirectAnswer | SubmitProbeReply | FinishProbe | RetryInterpretation | UsePendingAnswer


LegacyAction = Literal[
    "start", "restart", "retry", "retry_coaching", "prepare_research_plan",
    "retry_research_plan", "approve_research_plan", "end_defense", "end_unavailable",
]


@dataclass(frozen=True)
class LegacyCommand:
    """Temporary bridge for the existing workflows, removed as each migrates."""

    action: LegacyAction
    payload: Mapping[str, object]


Command = CastVote | SendChat | LegacyCommand | GenerateQuestion | CatchUpDeadline | SubmissionCommand | InterpretSubmission


def decode_command(message: dict) -> Command:
    action = message.get("type")
    if action == "cast_vote":
        return CastVote(message.get("seat"))
    if action == "send_chat":
        return SendChat(message.get("text"))
    if action == "submit_answer":
        return SubmitAnswer(message.get("turn"), message.get("answer"))
    if action == "submit_direct_answer":
        return SubmitDirectAnswer(message.get("turn"), message.get("answer"))
    if action == "submit_probe_reply":
        return SubmitProbeReply(message.get("turn"), message.get("answer"), message.get("probe_id"), message.get("direct") is True)
    if action == "finish_probe":
        return FinishProbe(message.get("turn"), message.get("probe_id"))
    if action == "retry_interpretation":
        return RetryInterpretation()
    if action == "use_pending_as_answer":
        return UsePendingAnswer()
    if action in get_args(LegacyAction):
        return LegacyCommand(action, MappingProxyType(dict(message)))
    raise ValueError("Unknown room action.")


@dataclass(frozen=True)
class CommandResult:
    accepted: bool
    error: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class VerifiedActor:
    """Identity established by server token/session checks for this invocation."""

    token: str
    account_id: str | None = None
