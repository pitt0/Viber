from __future__ import annotations

from typing import Any, Callable, Optional, override


class _MissingSentinel:
    __slots__ = ()

    def __eq__(self, _) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __repr__(self) -> str:
        return "..."


class _MissingURL(_MissingSentinel):

    @override
    def __repr__(self) -> str:
        return "http://127.0.0.1"

    def __str__(self) -> str:
        return "http://127.0.0.1"


MISSING: Any = _MissingSentinel()
MISSING_URL: Any = _MissingURL()


class Maybe[T]:

    def __init__(self, value: Optional[T]) -> None:
        self.value = value

    def bind[U](self, p: Callable[[T], Maybe[U]]) -> Maybe[T] | Maybe[U]:
        return self if self.value is None else p(self.value)

    def unwrap(self) -> T:
        if self.value is None:
            raise ValueError("Tried unwrapping None value")
        return self.value
    
    def unwrap_or(self, default: T) -> T:
        return self.value or default
