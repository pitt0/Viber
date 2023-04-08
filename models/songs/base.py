from functools import cached_property
from typing import Any, Self, Sequence
from typing import TypeVar

import discord

import models.requests.web.genius as gl
import models.requests.web.youtube as yt

from models.typing import Field


__all__ = (
    "Album",
    "Artist",
    "Track",

    "S"
)


S = TypeVar("S", bound="Track")


class Artist:

    def __init__(self, id: Any, name: str, url: str):
        self.id = id
        self.name = name
        self.url = url

    @cached_property
    def href(self) -> str:
        return f"({self.name})[{self.url}]" if self.url else self.name

    @classmethod
    def create(cls, data: Any) -> Self:
        raise NotImplementedError



class Album:

    def __init__(self, id: Any, name: str, authors: Sequence[Artist], thumbnail: str, release_date: str, url: str):
        self.id = id
        self.name = name
        self.authors = authors
        self.thumbnail = thumbnail
        self.release_date = release_date
        self.url = url

    async def dump(self) -> None:
        raise NotImplementedError

    @classmethod
    def create(cls, data: Any) -> Self:
        raise NotImplementedError



class Track:

    def __init__(self, id: Any, title: str, authors: Sequence[Artist], album: Album, duration: str, url: str):
        self.id = id
        self.title = title
        self.author = authors[0]
        self.artists = authors
        self.album = album
        self.duration = duration
        self.url = url

    def __str__(self) -> str:
        return f"{self.title} by {self.author}"

    def __repr__(self) -> str:
        return f"{self.title}#{self.id}"
    
    @cached_property
    def release_date(self) -> str:
        return self.album.release_date

    @cached_property
    def as_field(self) -> Field:
        return {"name": self.title, "value": self._embed_artists, "inline": True}

    @cached_property
    def embed(self) -> discord.Embed:
        return discord.Embed(
            title=self.title,
            description=self._embed_artists,
            color=discord.Colour.dark_purple()
        )

    @cached_property
    def lyrics(self) -> discord.Embed:
        song = gl.search(str(self))['hits'][0]['result']
        return discord.Embed(
            title=self.title,
            description=gl.lyrics(song['id']),
            color=discord.Colour.dark_purple()
        )

    @cached_property
    def source(self) -> str:
        print(f'Fetching source url of {self}') # NOTE: Log
        song = yt.search(f"{self.author.name} {self.title}", 'songs')[0]
        return yt.source(f"https://www.youtube.com/watch?v={song['videoId']}")

    @cached_property
    def _embed_artists(self) -> str:
        return ", ".join(artist.href for artist in self.artists)
    
    async def dump(self) -> None:
        raise NotImplementedError

    @classmethod
    def load(cls, id: Any) -> Self:
        """Gets song data stored in the database."""
        raise NotImplementedError

    @classmethod
    def create(cls, data: Any) -> Self:
        """Creates a `Track` instance from a specific api data."""
        raise NotImplementedError

    @classmethod
    def get(cls, url: str) -> Any:
        """Retrieves data starting from `url` string."""
        raise NotImplementedError

    @classmethod
    def search(cls, query: str, limit: int) -> Any:
        """Looks any api for data of the `query`, and returns `limit` number of song data found."""
        raise NotImplementedError

    @classmethod
    def find(cls, query) -> Self:
        """Creates a `Track` instance using `search` and then `create`"""
        return cls.create(cls.search(query, 1))

    def exists(self) -> bool:
        raise NotImplementedError