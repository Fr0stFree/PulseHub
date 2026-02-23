import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import random
import time

from common.logs.interface import LoggerLike


@dataclass(frozen=True)
class BackoffPolicy:
    base_delay_s: float = 1.0
    max_delay_s: float = 10.0
    multiplier: float = 2.0
    timeout_s: float = 60.0
    jitter_ratio: float = 0.2


class AsyncBackoff[T]:
    def __init__(self, name: str, logger: LoggerLike | None = None, policy: BackoffPolicy = BackoffPolicy()):
        self._name = name
        self._logger = logger
        self._policy = policy

    async def run(self, operation: Callable[[], Awaitable[T]]) -> T:
        start = time.monotonic()
        delay = self._policy.base_delay_s
        attempt = 0

        while True:
            attempt += 1
            try:
                return await operation()
            except Exception as exc:
                elapsed = time.monotonic() - start
                if elapsed >= self._policy.timeout_s:
                    raise RuntimeError(f"{self._name} not ready after {self._policy.timeout_s:.1f}s") from exc

                if self._logger:
                    self._logger.warning(
                        "Attempt %d: %s is not ready yet (error: %s). Retrying in %.1f seconds...",
                        attempt,
                        self._name,
                        exc,
                        delay,
                    )
                jitter = random.uniform(0.0, delay * self._policy.jitter_ratio)
                await asyncio.sleep(delay + jitter)
                delay = min(self._policy.max_delay_s, delay * self._policy.multiplier)
