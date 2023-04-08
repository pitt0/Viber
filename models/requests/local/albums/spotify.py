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
    async def _upload_album(id: str, name: str, thumbnail: str, release_date: str) -> None:
        async with (
            aiosqlite.connect('database/music.sqlite') as db,
            db.cursor() as cursor
        ):
            await cursor.execute('select rowid, thumbnail from albums where album_name = ? and release_date = ?;', (name, release_date))
            if (res := await cursor.fetchone()) is not None:
                query = ''
                if res[1] is None:
                    query = 'update albums set thumbnail = ? where album_name = ? and release_date like ?;'
                    await cursor.execute(query, (thumbnail, name, release_date))
                
                query = (
                    'update external_album_ids ' 
                    'set spotify_id = ? '
                    'where album_id = ?;'
                )
                await cursor.execute(query, (id, res[0]))
            else:
                query = (
                    'insert into albums '
                    'values (?, ?, ?);'
                )
                await cursor.execute(query, (name, release_date, thumbnail))
                query = (
                    'insert into external_album_ids (album_id, spotify_id) '
                    'values ((select rowid from albums where album_name = ? and release_date = ?), ?);'
                )
                await cursor.execute(query, (name, release_date, id))
            await db.commit()


    @staticmethod
    async def _upload_artists(artists: Iterable) -> None:
        async with (
            aiosqlite.connect('database/music.sqlite') as db,
            db.cursor() as cursor
        ):
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
            await db.commit()
    
    @classmethod
    async def dump(cls, id: str, name: str, artists: Iterable, thumbnail: str, release_date: str) -> None:
        await asyncio.gather(
            cls._upload_album(id, name, thumbnail, release_date),
            cls._upload_artists(artists)
        )

        async with (
            aiosqlite.connect('database/music.sqlite') as db,
            db.cursor() as cursor
        ):
            for artist in artists:
                await cursor.execute((
                    'insert or ignore into album_authors '
                    'values ((select rowid from albums where album_name = ? and release_date like ?), (select rowid from artists_ids where spotify_id = ?));'
                    ), 
                    (name, release_date, artist.id))

            await db.commit()