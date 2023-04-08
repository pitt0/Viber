import aiosqlite
import asyncio
from typing import Iterable
from resources.connections import Connection


class SpotifyRequest:

    @staticmethod
    def get(id: str) -> list[tuple[str, str, str, str, str]]:
        with Connection() as cursor:
            query = (
                'select song_title, external_album_ids.spotify_id, artist_name, songs.duration, artists_ids.spotify_id as sp_art_id '
                'from songs inner join external_ids on external_ids.song_id = songs.rowid '
                'inner join external_album_ids on external_album_ids.album_id = songs.album_id '
                'inner join song_authors on song_authors.song_id = songs.rowid '
                'inner join artists_ids on song_authors.artist_id = artists_ids.rowid '
                'where external_ids.spotify_id = ?;'
            )
            cursor.execute(query, (id,))
            return cursor.fetchall()


    @staticmethod
    async def _update_song(cursor: aiosqlite.Cursor,id: str, title: str, album_id: int, duration: str) -> None:
        await cursor.execute('select rowid from songs where song_title = ? and album_id = ?;', (title, album_id))
        if (song_id := await cursor.fetchone()) is not None:
            print(f'Song `{title}` found in database, updating info.')
            query = (
                'update external_ids set spotify_id = ? '
                'where not exists spotify_id and song_id = ?;'
            )
            params = (id, song_id[0])
        else:
            print(f'Song `{title}` not found in database, uploading to database.')
            query = (
                'insert into songs '
                'values (?, ?, ?); '
                'insert into external_ids (song_id, spotify_id) values ((select rowid from songs where song_title = ? and album_id = ?), ?);'
            )
            params = (title, album_id, duration, title, album_id, id)

        await cursor.execute(query, params)
        print(f'Song `{title}` uploaded.')

    @staticmethod
    async def _upload_artists(cursor: aiosqlite.Cursor, artists: Iterable) -> None:
        for artist in artists:
            print(f'Uploading artist {artist.name}')
            await cursor.execute('select 1, spotify_id from artists_ids where artist_name = ?;', (artist.name))
            if (res := await cursor.fetchone()) is not None:
                if res[1] is not None:
                    continue
                query = 'update artists_ids set spotify_id = ? where artist_name = ?;'
                params = (artist.id, artist.name)

            else:
                query = 'insert into artists_ids (artist_name, spotify_id) values (?, ?);'
                params = (artist.name, artist.id)

            await cursor.execute(query, params)
        print('Arists uploaded.')

    @classmethod
    async def dump(cls, id: str, title: str, album_id: int, artists: Iterable, duration: str) -> None:
        async with (
            aiosqlite.connect('database/music.sqlite') as db,
            db.cursor() as cursor
        ):
            print(f'Dumping song `{title}`.')
            await asyncio.gather(
                cls._update_song(cursor, id, title, album_id, duration),
                cls._upload_artists(cursor, artists)
            )
            await db.commit()

            for artist in artists:
                await cursor.execute((
                    'insert into song_authors '
                    'values ((select rowid from songs where song_title = ? and album_id = ?), ?) '
                    'where not exists ((select rowid from songs where song_title = ? and album_id = ?), ?);'
                    ), 
                    (title, album_id, artist.id, title, album_id, artist.id))

            await db.commit()