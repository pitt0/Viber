import json
import sqlite3 as sql


__all__ = (
    'Connector',
    'PlaylistCacheReader',
    'PlaylistCacheEditor'
)

class Connector:

    def __init__(self):
        self.connection = sql.connect('database/music.sqlite')

    def __enter__(self):
        return self.connection.cursor()

    def __exit__(self, *args):
        self.connection.commit()
        self.connection.close()

class PlaylistCacheReader:

    def __init__(self):
        self.file = open('database/playlist_cache.json')
    
    def __enter__(self):
        return json.load(self.file)

    def __exit__(self, *args):
        return self.file.__exit__(*args)

class PlaylistCacheEditor:

    def __init__(self):
        self.file = open('database/playlist_cache.json', 'w')

    def __enter__(self):
        return self.file.__enter__()

    def __exit__(self, *args):
        return self.file.__exit__(*args)

class SongCacheReader:

    def __init__(self):
        self.file = open('database/song_cache.json')

    def __enter__(self):
        return json.load(self.file)

    def __exit__(self, *args):
        return self.file.__exit__(*args)

class SongCacheEditor:

    def __init__(self):
        self.file = open('database/song_cache.json', 'w')

    def __enter__(self):
        return self.file.__enter__()

    def __exit__(self, *args):
        return self.file.__exit__(*args)