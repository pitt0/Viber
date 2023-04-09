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
            await cursor.execute('select rowid, thumbnail from albums where album_name = ? and release_date = ?;', (name, release_date))
            if (res := await cursor.fetchone()) is not None:
                album_id = res[0]
                if res[1] is None:
                    await cursor.execute('update albums set thumbnail = ? where album_name = ? and release_date like ?;', (thumbnail, name, release_date))

                await cursor.execute('update external_album_ids set youtube_id = ? where album_id = ?;', (youtube_id, album_id))

            else:
                await cursor.execute('insert into albums values (?, ?, ?) returning rowid;', (name, release_date, thumbnail))
                album_id = (await cursor.fetchone())[0] # type: ignore

                await cursor.execute('insert into external_album_ids (album_id, youtube_id) values (?, ?);', (album_id, youtube_id))

            await db.commit()
        return album_id


    @staticmethod
    async def _upload_artists(artists: Iterable) -> list[int]:
        async with (
            aiosqlite.connect('database/music.sqlite') as db,
            db.cursor() as cursor
        ):
            ids = []
            for artist in artists:
                params = {'name': artist.name, 'id': artist.id}
                await cursor.execute('select 1, youtube_id from artists_ids where artist_name = :name;', params)
                if (res := await cursor.fetchone()) is not None:
                    ids.append(res[0])
                    if res[1] is not None:
                        continue
                    await cursor.execute('update artists_ids set youtube_id = ? where artist_name = ?;', (artist.id, artist.name))

                else:
                    await cursor.execute('insert into artists_ids (artist_name, youtube_id) values (?, ?) returning rowid;', (artist.name, artist.id))
                    ids.append((await cursor.fetchone())[0]) # type: ignore

            await db.commit()
        return ids

    
    @classmethod
    async def dump(cls, id: str, name: str, artists: Iterable, thumbnail: str, release_date: str) -> None:
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