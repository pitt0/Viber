from resources.connections import Connection


class LocalAlbumRequest:

    @staticmethod
    def get(id: int) -> list[tuple[int, str, str, str, str, str, str]]:
        with Connection() as cursor:
            query = (
                'select albums.rowid, album_name, artist_name, release_date, thumbnail, external_album_ids.spotify_id, artists_ids.spotify_id as sp_artist_id '
                'from albums inner join external_album_ids on external_album_ids.album_id = albums.rowid '
                'inner join album_authors on album_authors.album_id = albums.rowid '
                'inner join artists_ids on album_authors.artist_id = artists_ids.rowid '
                'where albums.rowid = ?;'
            )
            cursor.execute(query, (id,))
            return cursor.fetchall()