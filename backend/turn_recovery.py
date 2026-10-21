"""One retained validated question plan, fenced by work and logical input identity.

The coordinator claims work before a provider thread starts. Invalidation revokes
old claims immediately; a manual retry may retain the plan without retaining the
old thread's authority. No source text or plan is published by this module.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from threading import Lock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.defense_session import PlannedMove


class StaleQuestionWork(RuntimeError):
    pass


@dataclass(frozen=True)
class QuestionPlanLease:
    _owner: QuestionPlanRecovery = field(repr=False)
    _token: object = field(repr=False)

    @property
    def current(self) -> bool:
        with self._owner._lock:
            return self._owner._token is self._token

    def bind(self, identity: str) -> PlannedMove | None:
        with self._owner._lock:
            self._check()
            if self._owner._identity != identity:
                self._owner._identity, self._owner._plan = identity, None
            self._owner._stage = 'writing' if self._owner._plan is not None else 'planning'
            return deepcopy(self._owner._plan)

    def remember(self, plan: PlannedMove) -> None:
        with self._owner._lock:
            self._check()
            self._owner._plan = deepcopy(plan)
            self._owner._stage = 'writing'

    def complete(self) -> None:
        with self._owner._lock:
            self._check()
            self._owner._identity = self._owner._plan = self._owner._stage = None

    def _check(self) -> None:
        if self._owner._token is not self._token:
            raise StaleQuestionWork('This question work is no longer current.')


class QuestionPlanRecovery:
    def __init__(self):
        self._lock = Lock()
        self._token = object()
        self._namespace = None
        self._identity = None
        self._plan = None
        self._stage = None

    def claim(self, namespace: str) -> QuestionPlanLease:
        with self._lock:
            if namespace != self._namespace:
                self._identity = self._plan = self._stage = None
                self._namespace = namespace
            self._token = object()
            return QuestionPlanLease(self, self._token)

    def seed(self, namespace: str, identity: str, plan: "PlannedMove") -> None:
        with self._lock:
            if namespace != self._namespace:
                self._namespace = namespace
            self._token = object()
            self._identity = identity
            self._plan = deepcopy(plan)
            self._stage = 'writing'

    def invalidate(self, *, keep_plan: bool = False) -> None:
        with self._lock:
            self._token = object()
            if not keep_plan:
                self._identity = self._plan = self._stage = None

    @property
    def stage(self) -> str | None:
        with self._lock:
            return self._stage
