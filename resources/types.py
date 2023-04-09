from typing import Any

# generic
class _MissingSentinel:
    __slots__ = ()

    def __eq__(self, other) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __repr__(self):
        return '...'
    

class _MissingURL(_MissingSentinel):

    def __repr__(self):
        return "http://127.0.0.1"

    def __str__(self):
        return "http://127.0.0.1"

    
MISSING: Any = _MissingSentinel()
MISSING_URL: Any = _MissingURL()