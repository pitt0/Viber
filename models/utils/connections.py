from typing import Any
import sqlite3 as sql
import json


__all__ = (
    'Connector',
    'PlaylistCache',
    'SongCache'
)

class Connector:

    def __init__(self):
        self.connection = sql.connect('database/music.sqlite')

    def __enter__(self):
        return self.connection.cursor()

    def __exit__(self, *args):
        self.connection.commit()
        self.connection.close()


class CacheFile:

    """Opens a file in both read and write mode and when exits it automatically dumps to cache."""

    file: str

    cache: dict[str, Any]

    def __enter__(self) -> dict[str, Any]:
        with open(self.file) as f:
            self.cache = json.load(f)
            return self.cache

    def __exit__(self, *args):
        with open(self.file, 'w') as f:
            json.dump(self.cache, f, indent=4)


class PlaylistCache(CacheFile):

    file = 'database/playlist_cache.json'


class SongCache(CacheFile):

    file = 'database/song_cache.json'
