from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass


ERROR_KEYWORDS = (
    "error",
    "exception",
    "failed",
    "failure",
    "panic",
    "fatal",
)


def is_error(line: str) -> bool:
    lowered = line.lower()
    return any(term in lowered for term in ERROR_KEYWORDS)


@dataclass
class SlidingWindowDetector:
    window_seconds: int = 120
    threshold: int = 3
    cooldown_seconds: int = 300

    def __post_init__(self) -> None:
        self._seen: dict[str, deque] = defaultdict(deque)
        self._last_triggered: dict[str, float] = {}

    def _now(self) -> float:
        return time.time()

    def _prune(self, pattern: str, now: float) -> None:
        q = self._seen[pattern]
        while q and now - q[0] > self.window_seconds:
            q.popleft()

    def update_window(self, pattern: str, event_ts: float | None = None) -> int:
        now = event_ts or self._now()
        self._prune(pattern, now)
        self._seen[pattern].append(now)
        return len(self._seen[pattern])

    def should_trigger(self, pattern: str, count: int | None = None, event_ts: float | None = None) -> bool:
        now = event_ts or self._now()
        self._prune(pattern, now)
        current = count if count is not None else len(self._seen[pattern])
        if current < self.threshold:
            return False

        last = self._last_triggered.get(pattern)
        if last is not None and now - last < self.cooldown_seconds:
            return False

        self._last_triggered[pattern] = now
        return True

