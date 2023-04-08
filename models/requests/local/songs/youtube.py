import aiosqlite
import asyncio
from typing import Iterable
from resources.connections import Connection


class YouTubeRequest:

    @staticmethod
    def get(id: str) -> list[tuple[str, str, str, str, str]]:
        with Connection() as cursor:
            query = (
                'select song_title, external_album_ids.youtube_id, artist_name, songs.duration, artists_ids.youtube_id as yt_art_id '
                'from songs inner join external_ids on external_ids.song_id = songs.rowid '
                'inner join external_album_ids on external_album_ids.album_id = songs.album_id '
                'inner join song_authors on song_authors.song_id = songs.rowid '
                'inner join artists_ids on song_authors.artist_id = artists_ids.rowid '
                'where external_ids.youtube_id = ?;'
            )
            cursor.execute(query, (id,))
            return cursor.fetchall()


    @staticmethod
    async def _update_song(id: str, title: str, album_id: int, duration: str) -> None:
        async with (
            aiosqlite.connect('database/music.sqlite') as db,
            db.cursor() as cursor
        ):
            await cursor.execute('select rowid from songs where song_title = ? and album_id = ?;', (title, album_id))
            if (song_id := await cursor.fetchone()) is not None:
                query = (
                    'update external_ids set youtube_id = ? '
                    'where song_id = ?;'
                )
                params = (id, song_id[0])
            else:
                query = (
                    'insert into songs '
                    'values (?, ?, ?); '
                    'insert into external_ids (song_id, youtube_id) values ((select rowid from songs where song_title = ? and album_id = ?), ?);'
                )
                params = (title, album_id, duration, title, album_id, id)

            await cursor.execute(query, params)
            await db.commit()

    @staticmethod
    async def _upload_artists(artists: Iterable) -> None:
        async with (
            aiosqlite.connect('database/music.sqlite') as db,
            db.cursor() as cursor
        ):
            for artist in artists:
                await cursor.execute('select 1, youtube_id from artists_ids where artist_name = ?;', (artist.name))
                if (res := await cursor.fetchone()) is not None:
                    if res[1] is not None:
                        continue
                    query = 'update artists_ids set youtube_id = ? where artist_name = ?;'
                    params = (artist.id, artist.name)

                else:
                    query = 'insert into artists_ids (artist_name, youtube_id) values (?, ?);'
                    params = (artist.name, artist.id)

                await cursor.execute(query, params)
            await db.commit()

    @classmethod
    async def dump(cls, id: str, title: str, album_id: int, artists: Iterable, duration: str) -> int:
        await asyncio.gather(
            cls._update_song(id, title, album_id, duration),
            cls._upload_artists(artists)
        )

        async with (
            aiosqlite.connect('database/music.sqlite') as db,
            db.cursor() as cursor
        ):
            for artist in artists:
                await cursor.execute((
                    'insert into song_authors '
                    'values ((select rowid from songs where song_title = ? and album_id = ?), ?);'
                    ), 
                    (title, album_id, artist.id,))

            await db.commit()
            
            await cursor.execute('select song_id from external_ids where youtube_id = ?', (id,))
            return (await cursor.fetchone())[0] # type: ignore