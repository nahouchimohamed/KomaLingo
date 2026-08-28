from __future__ import annotations
import time
from contextlib import contextmanager

@contextmanager
def stage_timer(name: str, sink: dict[str, float]):
    start = time.perf_counter()
    try:
        yield
    finally:
        sink[name] = sink.get(name, 0.0) + (time.perf_counter() - start)
