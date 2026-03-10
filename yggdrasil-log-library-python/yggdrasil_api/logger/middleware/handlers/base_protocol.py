from typing import Protocol, runtime_checkable
from dataclasses import dataclass


@dataclass
class CounterResult:
    count: int
    failed_count: int = 0


@runtime_checkable
class YggDBHandler(Protocol):
    def reset(self) -> CounterResult: ...

    @property
    def count(self) -> int: ...
