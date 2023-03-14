from typing import Any
from typing import TypeAlias, TypedDict

import discord

# discord
GUILD_ID: TypeAlias = int
USER_ID: TypeAlias = int
USER: TypeAlias = discord.User | discord.Member

# music
SONG_ID: TypeAlias = str
PLAYLIST_BASE: TypeAlias = dict[str, dict[str, list[SONG_ID]]]

class Collection(TypedDict):
    songs: list[SONG_ID]

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