"""Closed room commands and server-verified invocation identity."""

from dataclasses import dataclass


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


@dataclass(frozen=True)
class PrepareResearchPlan:
    retry: bool = False
    profile_correction: object = None


@dataclass(frozen=True)
class ApproveResearchPlan:
    plan_id: object
    question_budget: object
    confirm_profile: bool = False
    acknowledge_uncertainty: bool = False


@dataclass(frozen=True)
class GenerateResearchPlan:
    generation_id: int


@dataclass(frozen=True)
class RetryCoaching:
    pass


@dataclass(frozen=True)
class GenerateCoaching:
    generation_id: int


@dataclass(frozen=True)
class PublishRoom:
    pass


@dataclass(frozen=True)
class ObserveAbsence:
    pass


@dataclass(frozen=True)
class JoinDefender:
    token: str
    name: str


@dataclass(frozen=True)
class DefenderConnected:
    socket: object


@dataclass(frozen=True)
class DefenderDisconnected:
    token: str
    socket: object


PlanCommand = PrepareResearchPlan | ApproveResearchPlan
SubmissionCommand = SubmitAnswer | SubmitDirectAnswer | SubmitProbeReply | FinishProbe | RetryInterpretation | UsePendingAnswer


@dataclass(frozen=True)
class StartDefense:
    plan_id: object = None
    question_budget: object = None
    confirm_cost: bool = False


@dataclass(frozen=True)
class RestartDefense:
    confirm_cost: bool = False


@dataclass(frozen=True)
class ChooseOpening:
    candidate_id: object
    accept: bool


@dataclass(frozen=True)
class RetryQuestion:
    pass


@dataclass(frozen=True)
class EndDefense:
    pass


@dataclass(frozen=True)
class EndUnavailable:
    pass


@dataclass(frozen=True)
class ReclaimRoom:
    expired_only: bool = False


LifecycleCommand = StartDefense | RestartDefense | RetryQuestion | EndDefense | EndUnavailable


Command = ChooseOpening | CastVote | SendChat | LifecycleCommand | ReclaimRoom | GenerateQuestion | CatchUpDeadline | SubmissionCommand | InterpretSubmission | PlanCommand | GenerateResearchPlan | RetryCoaching | GenerateCoaching | PublishRoom | ObserveAbsence | JoinDefender | DefenderConnected | DefenderDisconnected


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
    if action in {"prepare_research_plan", "retry_research_plan"}:
        return PrepareResearchPlan(retry=action == "retry_research_plan", profile_correction=message.get("profile_correction"))
    if action == "approve_research_plan":
        return ApproveResearchPlan(message.get("plan_id"), message.get("question_budget"),
                                   message.get("confirm_profile") is True,
                                   message.get("acknowledge_uncertainty") is True)
    if action == "retry_coaching":
        return RetryCoaching()
    if action == "start":
        return StartDefense(message.get("plan_id"), message.get("question_budget"), message.get("confirm_cost") is True)
    if action == "restart":
        return RestartDefense(message.get("confirm_cost") is True)
    if action in {"accept_repeated_opening", "retry_opening"}:
        return ChooseOpening(message.get("candidate_id"), action == "accept_repeated_opening")
    if action == "retry":
        return RetryQuestion()
    if action == "end_defense":
        return EndDefense()
    if action == "end_unavailable":
        return EndUnavailable()
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
