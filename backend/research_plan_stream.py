"""Read complete topic objects from one structured output, never partial text."""

import json
import re

from backend.question_generator import QuestionGenerationError


class CompletedTopicDecoder:
    def __init__(self):
        self._buffer = ""
        self._started = False
        self._finished = False
        self._received = 0
        self._topic: list[str] = []
        self._depth = 0
        self._quoted = False
        self._escaped = False

    def feed(self, delta: str) -> list[dict]:
        self._received += len(delta)
        if self._received > 1_000_000:
            raise QuestionGenerationError("The AI research map is too large. Retry preparing the defense.")
        if self._finished:
            return []
        if not self._started:
            self._buffer += delta
            opening = re.match(r'\s*\{\s*"topics"\s*:\s*\[', self._buffer)
            if not opening:
                return []
            delta = self._buffer[opening.end():]
            self._buffer = ""
            self._started = True
        topics = []
        # Scan each character once, then decode only completed objects. Avoid
        # repeatedly reparsing a long unfinished string on every token delta.
        for character in delta:
            if not self._topic:
                if character in " \t\r\n,":
                    continue
                if character == "]":
                    self._finished = True
                    break
                if character != "{":
                    raise QuestionGenerationError("The AI returned invalid topic details. Retry preparing the defense.")
            self._topic.append(character)
            if self._quoted:
                if self._escaped:
                    self._escaped = False
                elif character == "\\":
                    self._escaped = True
                elif character == '"':
                    self._quoted = False
            elif character == '"':
                self._quoted = True
            elif character == "{":
                self._depth += 1
            elif character == "}":
                self._depth -= 1
                if self._depth == 0:
                    topics.append(json.loads("".join(self._topic)))
                    self._topic.clear()
        return topics
