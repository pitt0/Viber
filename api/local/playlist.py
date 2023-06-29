from resources import MISSING
from resources.connections import Connection
from typing import Literal


def dump(provider_id: str, provider: Literal['local', 'spotify', 'youtube'], title: str, target_id: int, author_id: int, privacy: int = 1) -> int:
    with Connection() as cursor:
        query = (
            'INSERT INTO playlists (playlist_title, target_id, author_id, privacy) '
            'VALUES (?, ?, ?, ?) RETURNING rowid;'
        )
        cursor.execute(query, (title, target_id, author_id, privacy))
        rowid = cursor.fetchone()[0]

        if provider != 'local':
            cursor.execute(f'INSERT INTO external_playlist_ids (playlist_id, {provider}_id) VALUES (?, ?);', (rowid, provider_id))

        cursor.execute('INSERT INTO playlist_owners (playlist_id, owner_id, permission_lvl) VALUES (?, ?, 4);', (rowid, author_id))

        return rowid
    

def get(id: int = MISSING, title: str = MISSING, target: int = MISSING) -> tuple[int, str, int, int, str, int]:
    with Connection() as cursor:
        query = (
            'SELECT rowid, playlist_title, target_id, author_id, creation_date, privacy '
            'FROM playlists '
            'WHERE rowid = ? OR (playlist_title = ? AND target_id = ?);'
        )
        params = (id or None, title or None, target or None)

        cursor.execute(query, params)
        return cursor.fetchone()
