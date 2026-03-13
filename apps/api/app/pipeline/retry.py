from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


def with_retries(fn: Callable[[], T], *, attempts: int = 3, base_delay: float = 0.4) -> T:
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - provider HTTP errors vary
            last_exc = exc
            if attempt + 1 >= attempts:
                break
            delay = base_delay * (2**attempt)
            logger.warning("retry %s/%s after error: %s", attempt + 1, attempts, exc)
            time.sleep(delay)
    assert last_exc is not None
    raise last_exc
