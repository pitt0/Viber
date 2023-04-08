import aiosqlite
import asyncio
from typing import Iterable
from resources.connections import Connection


class SpotifyAlbumRequest:

    @staticmethod
    def get(id: str) -> list[tuple[str, str, str, str, str]]:
        with Connection() as cursor:
            query = (
                'select album_name, artist_name, release_date, thumbnail, artists_ids.spoitfy_id '
                'from albums inner join external_album_ids on external_album_ids.album_id = albums.rowid '
                'inner join album_authors on album_authors.album_id = albums.rowid '
                'inner join artists_ids on artist_id = artists_ids.rowid '
                'where external_album_ids.spotify_id = ?;'
            )
            cursor.execute(query, (id,))
            return cursor.fetchall()
        

    @staticmethod
    async def _upload_album(cursor: aiosqlite.Cursor, id: str, name: str, thumbnail: str, release_date: str) -> None:
        params = {'name': name, 'rd': release_date, 'thumbnail': thumbnail, 'id': id}
        await cursor.execute('select 1, thumbnail from albums where album_name = :name and release_date like %:rd;', (name, release_date))
        # NOTE: '1' is needed in case the album is present and thumbnail is None
        if (res := await cursor.fetchone()) is not None:
            query = ''

            if res[1] is None:
                query = 'update albums set thumbnail = :thumbnail where album_name = :name and release_date like %:rd; '
                params = (thumbnail, name, release_date)
            
            query += (
                'update external_album_ids ' 
                'inner join albums on albums.rowid = album_id ' 
                'set spotify_id = :id '
                'where album_name = :name and release_date like %:rd and spotify_id = null;'
            )
        else:
            query = (
                'insert into albums '
                'values (:name, :rd, :thumbnail); '
                'insert into external_album_ids (album_id, spotify_id) '
                'values ((select rowid from albums where album_name = :name and release_date = :rd), :id);'
                )
            params = {'name': name, 'rd': release_date, 'thumbnail': thumbnail, 'id': id}

        await cursor.execute(query, params)

    @staticmethod
    async def _upload_artists(cursor: aiosqlite.Cursor, artists: Iterable) -> None:
        for artist in artists:
            params = {'name': artist.name, 'id': artist.id}
            await cursor.execute('select 1, spotify_id from artists_ids where artist_name = :name;', params)
            if (res := await cursor.fetchone()) is not None:
                if res[1] is not None:
                    continue
                query = 'update artists_ids set spotify_id = :id where artist_name = :name;'

            else:
                query = 'insert into artists_ids (artist_name, spotify_id) values (:name, :id);'

            await cursor.execute(query, params)
    
    @classmethod
    async def dump(cls, id: str, name: str, artists: Iterable, thumbnail: str, release_date: str) -> None:
        async with (
            aiosqlite.connect('database/music.sqlite') as db,
            db.cursor() as cursor
        ):
            await asyncio.gather(
                cls._upload_album(cursor, id, name, thumbnail, release_date),
                cls._upload_artists(cursor, artists)
            )
            await db.commit()

            for artist in artists:
                await cursor.execute((
                    'insert into album_authors '
                    'values ((select rowid from albums where album_name = ? and release_date like %?), ?) '
                    'where not exists ((select rowid from albums where album_name = ? and release_date like %?), ?);'
                    ), 
                    (name, release_date, artist.id, name, release_date, artist.id))

            await db.commit()