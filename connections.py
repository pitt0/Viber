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
        print('Opening Database')
        return self.connection.cursor()

    def __exit__(self, *args):
        print('Committing...')
        self.connection.commit()
        print("Closing Database")
        self.connection.close()


class CacheFile:

    """Opens a file in both read and write mode and when exits it automatically dumps to cache."""

    folder: str = 'database/cache/'
    file: str

    cache: dict[str, Any]

    def __enter__(self) -> dict[str, Any]:
        with open(self.folder + self.file) as f:
            self.cache = json.load(f)
            return self.cache

    def __exit__(self, *args):
        with open(self.folder + self.file, 'w') as f:
            json.dump(self.cache, f, indent=4)


class PlaylistCache(CacheFile):

    file = 'playlists.json'

class AdvicesCache(CacheFile):

    file = 'advices.json'

class LikedSongsCache(CacheFile):

    file = 'liked_songs.json'

class SongCache(CacheFile):

    file = 'songs.json'
