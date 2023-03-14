from typing import overload

import sqlite3 as sql
import json

from .typings import Collection


__all__ = (
    "Devs",
    "Connector",
    "CacheFile",
    "PlaylistCache",
    "AdvicesCache",
    "LikedSongsCache",
    "SongCache"
)

PLAYLIST_ID = str

class Connector:

    def __init__(self):
        self.connection = sql.connect("database/music.sqlite")

    def __enter__(self):
        return self.connection.cursor()

    def __exit__(self, *args):
        self.connection.commit()
        self.connection.close()


class Devs:

    file: str = "database/devs.json"

    cache: list[int]

    def __enter__(self) -> list[int]:
        with open(self.file) as f:
            self.cache = json.load(f)
            return self.cache

    def __exit__(self, *args):
        with open(self.file, "w") as f:
            json.dump(self.cache, f, indent=4)


class CacheFile:

    """Opens a file in both read and write mode and when exits it automatically dumps to cache."""

    folder: str = "database/cache/"
    file: str

    cache: dict[PLAYLIST_ID, Collection]

    def __enter__(self) -> dict[PLAYLIST_ID, Collection]:
        self.cache = {}
        with open(self.folder + self.file) as f:
            self.cache = json.load(f)
            return dict(self.cache)

    def __exit__(self, *_):
        with open(self.folder + self.file, "w") as f:
            json.dump(self.cache, f, indent=4)


class PlaylistCache(CacheFile):

    file = "playlists.json"

class AdvicesCache(CacheFile):

    file = "advices.json"

class LikedSongsCache(CacheFile):

    file = "liked_songs.json"

class SongCache(CacheFile):

    file = "songs.json"
    cache: dict[str, str]

    def __enter__(self) -> dict[str, str]:
        return super().__enter__() # type: ignore

    @overload
    @classmethod
    def load(cls, ref: str) -> bool:
        ...

    @overload
    @classmethod
    def load(cls, ref: None = None) -> dict[str, str]:
        ...

    @classmethod
    def load(cls, ref: str | None = None):
        with open(cls.folder + cls.file) as f:
            if ref:
                return ref in json.load(f)
            else:
                return json.load(f)