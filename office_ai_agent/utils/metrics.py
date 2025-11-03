from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Dict


class Metrics:
    """Lightweight in-process metrics with counters and simple timers."""

    def __init__(self) -> None:
        self.counters: Dict[str, int] = {}
        # timers[name] = {"count": int, "total": float}
        self.timers: Dict[str, Dict[str, float | int]] = {}

    def inc(self, key: str, value: int = 1) -> None:
        self.counters[key] = int(self.counters.get(key, 0)) + int(value)

    @contextmanager
    def timer(self, name: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            entry = self.timers.get(name)
            if entry is None:
                self.timers[name] = {"count": 1, "total": elapsed}
            else:
                entry["count"] = int(entry.get("count", 0)) + 1
                entry["total"] = float(entry.get("total", 0.0)) + float(elapsed)

    def snapshot(self) -> dict:
        # Provide avg for timers
        timers = {}
        for k, v in self.timers.items():
            count = int(v.get("count", 0))
            total = float(v.get("total", 0.0))
            avg = (total / count) if count else 0.0
            timers[k] = {"count": count, "total": total, "avg": avg}
        return {"counters": dict(self.counters), "timers": timers}
