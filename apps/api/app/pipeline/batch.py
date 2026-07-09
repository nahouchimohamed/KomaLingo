from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections.abc import Callable, Iterable
from typing import TypeVar
T = TypeVar("T"); R = TypeVar("R")

def map_parallel(items: Iterable[T], fn: Callable[[T], R], *, workers: int = 4) -> list[R]:
    seq = list(items)
    if not seq:
        return []
    workers = max(1, min(workers, len(seq)))
    results: list[R | None] = [None] * len(seq)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fn, item): idx for idx, item in enumerate(seq)}
        for fut in as_completed(futures):
            results[futures[fut]] = fut.result()
    return [r for r in results if r is not None]  # type: ignore[misc]
