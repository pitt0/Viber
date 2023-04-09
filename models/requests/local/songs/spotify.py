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
    async def _update_song(spotify_id: str, title: str, sp_album_id: str, duration: str) -> int:
        async with (
            aiosqlite.connect('database/music.sqlite') as db,
            db.cursor() as cursor
        ):
            # selects the rowid of a songs, None if the song is not registered
            query = (
                'select songs.rowid from songs '
                'inner join external_album_ids as ext on songs.album_id = ext.album_id '
                'where song_title = ? and spotify_id = ?;'
            )
            await cursor.execute(query, (title, sp_album_id))
            
            if (song_id := await cursor.fetchone()) is not None:
                await cursor.execute('update external_ids set spotify_id = ? where song_id = ?', (spotify_id, song_id[0]))

            else:
                # album is surely registered
                await cursor.execute('select album_id from external_album_ids where spotify_id = ?;', (sp_album_id,))
                album_id = (await cursor.fetchone())[0] # type: ignore

                await cursor.execute('insert into songs values (?, ?, ?) returning rowid;', (title, album_id, duration))
                song_id = await cursor.fetchone()
                
                await cursor.execute('inert into external_ids (song_id, spotify_id) values (?, ?);', (song_id[0], spotify_id)) # type: ignore

            await db.commit()

        return song_id[0] # type: ignore
            

    @staticmethod
    async def _upload_artists(artists: Iterable) -> list[int]:
        async with (
            aiosqlite.connect('database/music.sqlite') as db,
            db.cursor() as cursor
        ):
            ids = []
            for artist in artists:
                await cursor.execute('select 1, spotify_id from artists_ids where artist_name = ?;', (artist.name,))
                if (res := await cursor.fetchone()) is not None:
                    if res[1] is not None:
                        continue
                    query = 'update artists_ids set spotify_id = ? where artist_name = ? returning rowid;'
                    params = (artist.id, artist.name)

                else:
                    query = 'insert or ignore into artists_ids (artist_name, spotify_id) values (?, ?) returning rowid;'
                    params = (artist.name, artist.id)

                await cursor.execute(query, params)
                ids.append((await cursor.fetchone())[0]) # type: ignore

            await db.commit()
        return ids


    @classmethod
    async def dump(cls, id: str, title: str, album_id: str, artists: Iterable, duration: str) -> int:
        results = await asyncio.gather(
            cls._update_song(id, title, album_id, duration),
            cls._upload_artists(artists)
        )

        async with (
            aiosqlite.connect('database/music.sqlite') as db,
            db.cursor() as cursor
        ):
            for artist_id in results[1]:
                await cursor.execute('insert into song_authors values (?, ?);', (results[0], artist_id))

            await db.commit()

        return results[0]