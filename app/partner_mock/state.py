from __future__ import annotations

from collections import defaultdict, deque
from copy import deepcopy
from dataclasses import dataclass
from threading import Lock
from typing import Any


@dataclass
class Scenario:
    statuses: deque[int]
    delay_ms: int = 0


class PartnerState:
    def __init__(self) -> None:
        self._lock = Lock()
        self._scenarios: dict[str, Scenario] = {}
        self._attempts: dict[str, list[int]] = defaultdict(list)
        self._messages: dict[str, dict[str, Any]] = {}
        self._acks: dict[str, str] = {}

    def configure(self, message_id: str, statuses: list[int], delay_ms: int) -> None:
        with self._lock:
            self._scenarios[message_id] = Scenario(deque(statuses), delay_ms)

    def next_response(self, message_id: str) -> tuple[int, int]:
        with self._lock:
            scenario = self._scenarios.get(message_id)
            if scenario and scenario.statuses:
                status = scenario.statuses.popleft()
                delay_ms = scenario.delay_ms
            else:
                status = 202
                delay_ms = 0
            self._attempts[message_id].append(status)
            return status, delay_ms

    def store_success(self, message_id: str, message: dict[str, Any], ack_id: str) -> None:
        with self._lock:
            self._messages[message_id] = deepcopy(message)
            self._acks[message_id] = ack_id

    def inspect(self, message_id: str) -> dict[str, Any] | None:
        with self._lock:
            if message_id not in self._attempts and message_id not in self._messages:
                return None
            return {
                "message_id": message_id,
                "attempt_statuses": list(self._attempts.get(message_id, [])),
                "delivered_message": deepcopy(self._messages.get(message_id)),
                "ack_id": self._acks.get(message_id),
            }

    def reset(self) -> None:
        with self._lock:
            self._scenarios.clear()
            self._attempts.clear()
            self._messages.clear()
            self._acks.clear()
