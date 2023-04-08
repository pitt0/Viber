from resources.connections import Connection


class SongRequest:

    @staticmethod
    def get(id: int) -> list[tuple[str, int, str, str, str, str]]:
        with Connection() as cursor:
            query = (
                'select song_title, album_id, artist_name, songs.duration, external_ids.spotify_id, artists_ids.spotify_id as sp_artist_id '
                'from songs inner join song_authors on song_authors.song_id = songs.rowid '
                'inner join external_ids on external_ids.song_id = songs.rowid '
                'inner join artists_ids on song_authors.artist_id = artists_ids.rowid '
                'where songs.rowid=?;'
            )
            cursor.execute(query, (id,))
            return cursor.fetchall()