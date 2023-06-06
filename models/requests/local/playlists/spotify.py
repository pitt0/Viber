from resources import Connection


class SpotifyPlaylistRequest:

    @staticmethod
    def dump(spotify_id: str, title: str, target_id: int, author_id: int) -> int:
        with Connection() as cursor:
            query = (
                'insert into playlists (playlist_title, target_id, author_id, privacy) '
                'values (?, ?, ?, ?) returning rowid;'
            )
            cursor.execute(query, (title, target_id, author_id, 1))
            rowid = cursor.fetchone()[0]

            cursor.execute('insert into external_playlist_ids (playlist_id, spotify_id) values (?, ?);', (rowid, spotify_id))

            cursor.execute('insert into playlist_owners (playlist_id, owner_id, permission_lvl) values (?, ?, 4);', (rowid, author_id))

            return rowid