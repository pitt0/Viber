from datetime import datetime
from typing import Any
import sqlite3 as sql
import json


__all__ = (
    'Connector',
    'PlaylistCache',
    'AdvicesCache',
    'LikedSongsCache',
    'SongCache'
)

class Connector:

    def __init__(self):
        self.connection = sql.connect('database/music.sqlite')

    def __enter__(self):
        now = datetime.now()
        print(f"[{now.strftime('%H:%M:%S')}] Opening Database")
        return self.connection.cursor()

    def __exit__(self, *args):
        now = datetime.now()
        print(f"[{now.strftime('%H:%M:%S')}] Committing...")
        self.connection.commit()
        print(f"[{now.strftime('%H:%M:%S')}] Closing Database")
        self.connection.close()


class CacheFile:

    """Opens a file in both read and write mode and when exits it automatically dumps to cache."""

    folder: str = 'database/cache/'
    file: str

    cache: dict[str, Any]

    def __enter__(self) -> dict[str, Any]:
        now = datetime.now()
        print(f"[{now.strftime('%H:%M:%S')}] Opening {self.file}")
        with open(self.folder + self.file) as f:
            self.cache = json.load(f)
            return self.cache

    def __exit__(self, *args):
        now = datetime.now()
        print(f"[{now.strftime('%H:%M:%S')}] Committing to {self.file}...")
        with open(self.folder + self.file, 'w') as f:
            json.dump(self.cache, f, indent=4)
        print(f"[{now.strftime('%H:%M:%S')}] Closing {self.file}")


class PlaylistCache(CacheFile):

    file = 'playlists.json'

class AdvicesCache(CacheFile):

    file = 'advices.json'

class LikedSongsCache(CacheFile):

    file = 'liked_songs.json'

class SongCache(CacheFile):

    file = 'songs.json'
