from typing import NamedTuple, TypeAlias, TypedDict

import discord

# TypeVars
GUILD_ID: TypeAlias = int
USER_ID: TypeAlias = int
USER: TypeAlias = discord.User | discord.Member
PLAYLIST_BASE: TypeAlias = dict[str, "SongCollection"]


class SongCollection(TypedDict):
    songs: list[str]

class SongBase(NamedTuple):
    id: str
    title: str
    author: str
    album: str
    thumbnail: str
    duration: str
    year: int

    spotify: str = ""
    youtube: str = ""

    source: str = ""