from resources.connections import Connection
from resources.types import MISSING


class PlaylistRequest:

    @staticmethod
    def get(id: int = MISSING, title: str = MISSING, target: int = MISSING) -> tuple[int, str, int, int, str, int]:
        with Connection() as cursor:
            query = (
                'select rowid, playlist_title, target_id, author_id, creation_date, privacy '
                'from playlists '
                'where rowid = ? or (playlist_title = ? and target_id = ?);'
            )
            params = (id or None, title or None, target or None)

            cursor.execute(query, params)
            return cursor.fetchone()

    @staticmethod
    def songs(id: int) -> list[tuple[int]]:
        with Connection() as cursor:
            query = (
                'select song_id '
                'from playlist_songs '
                'where playlist_id = ?;'
            )
            params = (id,)

            cursor.execute(query, params)
            return cursor.fetchall()

    @staticmethod
    def owners(id: int) -> list[tuple[int, int]]:
        with Connection() as cursor:
            query = (
                'select owner_id, permission_lvl '
                'from playlist_owners '
                'where playlist_id = ?;'
            )
            params = (id,)

            cursor.execute(query, params)
            return cursor.fetchall()

    @staticmethod
    def add(playlist_id: int, song_id: int, user_id: int) -> None:
        with Connection() as cursor:
            # NOTE asserting song is already registered in database
            query = 'insert into playlist_songs (playlist_id, song_id, added_by) values (?, ?, ?);'
            params = (playlist_id, song_id, user_id)

            cursor.execute(query, params)

    @staticmethod
    def remove(playlist_id: int, song_id: int) -> None:
        with Connection() as cursor:
            query = 'delete from playlist_songs where playlist_id = ? and song_id = ?;'
            params = (playlist_id, song_id)

            cursor.execute(query, params)

    @staticmethod
    def dump(name: str, target_id: int, author_id: int, privacy: int) -> int:
        with Connection() as cursor:
            query = (
                'insert into playlists (playlist_title, target_id, author_id, privacy) '
                'values (?, ?, ?, ?) '
                'returning rowid;'
            )
            params = (name, target_id, author_id, privacy)

            cursor.execute(query, params)
            rowid = cursor.fetchone()[0]

            query = (
                'insert into playlist_owners (playlist_id, owner_id, permission_lvl) '
                'values (?, ?, 4);'
            )
            cursor.execute(query, (rowid, author_id))
        return rowid
    
    @staticmethod
    def rename(id: int, name: str) -> None:
        with Connection() as cursor:
            cursor.execute('update playlists set playlist_title = ? where rowid = ?;', (name, id))

    @staticmethod
    def delete(id: int) -> None:
        with Connection() as cursor:
            cursor.execute('delete from playlists where rowid = ?;', (id,))
            cursor.execute('delete from playlist_songs where playlist_id = ?;', (id,))
            cursor.execute('delete from playlist_owners where playlist_id = ?;', (id,))