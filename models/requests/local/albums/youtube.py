import aiosqlite
import asyncio
from typing import Iterable
from resources.connections import Connection



class YouTubeAlbumRequest:

    @staticmethod
    def get(id: str) -> list[tuple[str, str, str, str, str]]:
        with Connection() as cursor:
            query = (
                'select album_name, artist_name, release_date, thumbnail, artists_ids.youtube_id '
                'from albums '
                'inner join external_album_ids as aext on aext.album_id = albums.rowid '
                'inner join album_authors on album_authors.album_id = albums.rowid '
                'inner join artists_ids on artist_id = artists_ids.rowid '
                'where aext.youtube_id = ?;'
            )
            cursor.execute(query, (id,))
            return cursor.fetchall()


    @staticmethod
    async def _upload_album(youtube_id: str, name: str, thumbnail: str, release_date: str) -> int:
        async with (
            aiosqlite.connect('database/music.sqlite') as db,
            db.cursor() as cursor
        ):
            query = (
                'insert into albums values (:n, :rd, :t) '
                'on collision do update set thumbnail = :t returning rowid;'
            )
            await cursor.execute(query, {'n': name, 'rd': release_date, 't': thumbnail})
            rowid = await cursor.fetchone()[0] # type: ignore[non-null]

            query = (
                'insert into external_album_ids (album_id, youtube_id) values (:id, :yid) '
                'on collision do update set youtube_id = :yid;'
            )
            await cursor.execute(query, {'id': rowid, 'yid': youtube_id})

            await db.commit()
        return rowid


    @staticmethod
    async def _upload_artists(artists: Iterable) -> list[int]:
        async with (
            aiosqlite.connect('database/music.sqlite') as db,
            db.cursor() as cursor
        ):
            ids = []
            query = (
                'insert into artists_ids (artist_name, youtube_id) values (:n, :sid) '
                'on collsion do update set youtube_id = :sid returning rowid;'
            )
            for artist in artists:
                params = {'n': artist.name, 'sid': artist.id}
                
                await cursor.execute(query, params)
                ids.append((await cursor.fetchone())[0]) # type: ignore[non-null]

            await db.commit()
        return ids

    
    @classmethod
    async def dump(cls, id: str, name: str, artists: Iterable, thumbnail: str, release_date: str) -> int:
        results = await asyncio.gather(
            cls._upload_album(id, name, thumbnail, release_date),
            cls._upload_artists(artists)
        )

        async with (
            aiosqlite.connect('database/music.sqlite') as db,
            db.cursor() as cursor
        ):
            for artist_id in results[1]:
                await cursor.execute(('insert or ignore into album_authors values (?, ?);'), (results[0], artist_id))

            await db.commit()
        return results[0]