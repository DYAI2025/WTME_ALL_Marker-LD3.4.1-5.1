from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict
import time

@dataclass
class Counter:
    value: int = 0
    def inc(self, n: int = 1) -> None:
        self.value += n

@dataclass
class EWMA:
    alpha: float
    value: float = 0.5
    def update(self, x: float) -> float:
        self.value = self.alpha * x + (1 - self.alpha) * self.value
        return self.value

@dataclass
class Telemetry:
    counters: Dict[str, Counter] = field(default_factory=dict)
    ewhm: Dict[str, EWMA] = field(default_factory=dict)

    def inc(self, key: str, n: int = 1) -> None:
        self.counters.setdefault(key, Counter()).inc(n)

    def ewma(self, key: str, alpha: float, x: float) -> float:
        e = self.ewhm.setdefault(key, EWMA(alpha=alpha))
        return e.update(x)

    def snapshot(self) -> Dict[str, float]:
        return {**{k: v.value for k, v in self.counters.items()},
                **{k: v.value for k, v in self.ewhm.items()}}

    def emit(self, sink=print) -> None:
        ts = int(time.time())
        sink({"ts": ts, **self.snapshot()})
