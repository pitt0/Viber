from typing import overload

import sqlite3 as sql
import json

from .time import Time
from .typings import SongCollection


__all__ = (
    "Devs",
    "Connector",
    "CacheFile",
    "PlaylistCache",
    "AdvicesCache",
    "LikedSongsCache",
    "SongCache"
)

class Connector:

    def __init__(self):
        self.connection = sql.connect("database/music.sqlite")

    def __enter__(self):
        print(f"[{Time.now()}] Opening Database")
        return self.connection.cursor()

    def __exit__(self, *args):
        print(f"[{Time.now()}] Committing...")
        self.connection.commit()
        print(f"[{Time.now()}] Closing Database")
        self.connection.close()


class Devs:

    """Opens the Developers (devs.json) file and iterates through it."""

    file: str = "database/devs.json"

    cache: list[int]

    def __enter__(self) -> list[int]:
        print(f"[{Time.now()}] Opening {self.file}")
        with open(self.file) as f:
            self.cache = json.load(f)
            return self.cache

    def __exit__(self, *args):
        print(f"[{Time.now()}] Committing to {self.file}...")
        with open(self.file, "w") as f:
            json.dump(self.cache, f, indent=4)
        print(f"[{Time.now()}] Closing {self.file}")


class CacheFile:

    """Opens a file in both read and write mode and when exits it automatically dumps to cache."""

    folder: str = "database/cache/"
    file: str

    cache: dict[str, SongCollection]

    def __enter__(self) -> dict[str, SongCollection]:
        print(f"[{Time.now()}] Opening {self.file}")
        print()
        print(f"Cache before opening:")
        print(self.cache)
        print()
        with open(self.folder + self.file) as f:
            self.cache = json.load(f)
            print("Cache after opening:")
            print(self.cache)
            print()
            return self.cache

    def __exit__(self, *_):
        print(f"[{Time.now()}] Committing to {self.file}...")
        print()
        print("Cache before committing:")
        print(self.cache)
        with open(self.folder + self.file, "w") as f:
            json.dump(self.cache, f, indent=4)
        print(f"[{Time.now()}] Closing {self.file}")


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
        ...

    @overload
    def load(self, ref: str) -> bool:
        ...

    @overload
    def load(self, ref: None = None) -> dict[str, str]:
        ...

    def load(self, ref: str | None = None):
        with open(self.folder + self.file) as f:
            if ref:
                return ref in json.load(f)
            else:
                return json.load(f)