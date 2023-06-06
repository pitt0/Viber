import aiosqlite
import asyncio
from typing import Iterable
from resources.connections import Connection


class SpotifyRequest:

    @staticmethod
    def get(id: str) -> list[tuple[str, str, str, str, str]]:
        with Connection() as cursor:
            query = (
                'select song_title, aext.spotify_id, artist_name, songs.duration, artists_ids.spotify_id as sp_art_id '
                'from songs '
                'inner join external_ids as ext on ext.song_id = songs.rowid '
                'inner join external_album_ids as aext on aext.album_id = songs.album_id '
                'inner join song_authors on song_authors.song_id = songs.rowid '
                'inner join artists_ids on song_authors.artist_id = artists_ids.rowid '
                'where ext.spotify_id = ?;'
            )
            cursor.execute(query, (id,))
            return cursor.fetchall()


    @staticmethod
    async def _update_song(spotify_id: str, title: str, album_id: int, duration: str) -> int:
        async with (
            aiosqlite.connect('database/music.sqlite') as db,
            db.cursor() as cursor
        ):
            query = (
                'insert into songs values (:t, :aid, :d) '
                'on conflict do update set duration = :d ' # NOTE forced update so it returns rowid
                'returning rowid;'
            )
            await cursor.execute(query, {'t': title, 'aid': album_id, 'd': duration})
            rowid = (await cursor.fetchone())[0] # type: ignore[non-null]
            
            query = (
                'insert into external_ids (song_id, spotify_id) values (:id, :sid) '
                'on conflict do update set spotify_id = :sid;'
            )
            await cursor.execute(query, {'id': rowid, 'sid': spotify_id})

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
                'insert into artists_ids (artist_name, spotify_id) values (:n, :sid) '
                'on conflict do update set spotify_id = :sid '
                'returning rowid;'
            )
            for artist in artists:
                await cursor.execute(query, {'n': artist.name, 'sid': artist.id})
                ids.append((await cursor.fetchone())[0]) # type: ignore[non-null]

            await db.commit()
        return ids


    @classmethod
    async def dump(cls, id: str, title: str, album_id: int, artists: Iterable, duration: str) -> int:
        results = await asyncio.gather(
            cls._update_song(id, title, album_id, duration),
            cls._upload_artists(artists)
        )

        async with (
            aiosqlite.connect('database/music.sqlite') as db,
            db.cursor() as cursor
        ):
            for artist_id in results[1]:
                await cursor.execute('insert or ignore into song_authors values (?, ?);', (results[0], artist_id))

            await db.commit()

        return results[0]