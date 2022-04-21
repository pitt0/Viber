from typing import Any, TypeAlias


__all__ = (
    'GUILD_ID',
    'IDENTIFIER',
    'MISSING',
    'USER_ID'
)

IDENTIFIER = str | int
GUILD_ID: TypeAlias = int
USER_ID: TypeAlias = int

class _MissingSentinel:
    def __eq__(self, other):
        return False

    def __bool__(self):
        return False

    def __repr__(self):
        return '...'


MISSING: Any = _MissingSentinel()