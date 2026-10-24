"""Read complete topic objects from one structured output, never partial text."""

import json

from backend.question_generator import QuestionGenerationError


class CompletedTopicDecoder:
    """Read complete topic objects from one structured output, never partial text.

    Strict schema mode requires every property but does not fix their order, and
    providers differ, so the topics array is located wherever it appears in the
    top-level object rather than assumed to come first.
    """

    def __init__(self):
        self._started = False
        self._finished = False
        self._received = 0
        self._topic: list[str] = []
        self._depth = 0
        self._quoted = False
        self._escaped = False
        self._scan_quoted = False
        self._scan_escaped = False
        self._scan_state = "key"
        self._scan_key = ""
        self._skip_quoted = False
        self._skip_escaped = False
        self._skip_depth = 0

    def feed(self, delta: str) -> list[dict]:
        self._received += len(delta)
        if self._received > 1_000_000:
            raise QuestionGenerationError("The AI research map is too large. Retry preparing the defense.")
        if self._finished:
            return []
        topics = []
        # Scan each character once, then decode only completed objects. Avoid
        # repeatedly reparsing a long unfinished string on every token delta.
        for character in delta:
            if not self._started:
                self._locate(character)
                continue
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

    def _locate(self, character: str) -> None:
        """Find the top-level "topics" array wherever the provider emits it."""
        if self._skip_quoted:
            if self._skip_escaped:
                self._skip_escaped = False
            elif character == "\\":
                self._skip_escaped = True
            elif character == '"':
                self._skip_quoted = False
            return
        if self._skip_depth:
            if character == '"':
                self._skip_quoted = True
            elif character in "{[":
                self._skip_depth += 1
            elif character in "}]":
                self._skip_depth -= 1
            return
        if self._scan_quoted:
            if self._scan_escaped:
                self._scan_escaped = False
            elif character == "\\":
                self._scan_escaped = True
            elif character == '"':
                self._scan_quoted = False
                self._scan_state = "colon"
            else:
                self._scan_key += character
            return
        if self._scan_state == "colon":
            if character in " \t\r\n":
                return
            if character == ":":
                self._scan_state = "value"
            return
        if self._scan_state == "value":
            if character in " \t\r\n":
                return
            self._scan_state = "key"
            if self._scan_key == "topics":
                if character != "[":
                    raise QuestionGenerationError("The AI returned invalid topic details. Retry preparing the defense.")
                self._started = True
            elif character == '"':
                self._skip_quoted = True
            elif character in "{[":
                self._skip_depth = 1
            return
        if character in " \t\r\n,":
            return
        if character == '"':
            self._scan_quoted = True
            self._scan_key = ""
