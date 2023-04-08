from resources.connections import Connection
from resources.typings import MISSING


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
            query = 'insert into playlist_songs (playlist_id, song_id, added_by) values (:p_id, :s_id, :u_id);'
            params = {'p_id': playlist_id, 's_id': song_id, 'u_id': user_id}

            cursor.execute(query, params)

    @staticmethod
    def remove(playlist_id: int, song_id: int) -> None:
        with Connection() as cursor:
            query = 'remove from playlist_songs where playlist_id = :p_id and song_id = :s_id;'
            params = {'p_id': playlist_id, 's_id': song_id}

            cursor.execute(query, params)

    @staticmethod
    def dump(name: str, target_id: int, author_id: int, privacy: int) -> int:
        with Connection() as cursor:
            query = (
                'insert into playlists (playlist_title, target_id, author_id, privacy) '
                'values (:name, :t_id, :auth, :p);'
                'select rowid from playlists '
                'where playlist_title = :name and target_id = :t_id and author_id = :auth;'
            )
            params = {'name': name, 't_id': target_id, 'auth': author_id, 'p': privacy}

            cursor.execute(query, params)
            rowid = cursor.fetchone()[0]

            query = (
                'insert into playlist_owners (playlist_id, owner_id, permission_lvl) '
                'values (:p_id, :auth, 4);'
            )
            cursor.execute(query, {'p_id': rowid, 'auth': author_id})
            return rowid