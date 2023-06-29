import aiosqlite
import asyncio
from resources.connections import Connection
from typing import Iterable, Literal


async def update_song(provider_id: str, provider: Literal['spotify', 'youtube'], **data) -> int:
    async with (
        aiosqlite.connect('database/music.sqlite') as db,
        db.cursor() as cursor
    ):
        query = (
            'INSERT INTO songs VALUES (:title, :album_id, :duration) '
            'ON CONFLICT DO UPDATE SET duration = :duration ' # HACK forced update so it returns rowid
            'RETURNING rowid;'
        )
        await cursor.execute(query, data)
        rowid = (await cursor.fetchone())[0] # type: ignore[non-null]
        
        query = (
            f'INSERT INTO external_ids (song_id, {provider}_id) VALUES (:id, :sid) '
            f'ON CONFLICT DO UPDATE SET {provider}_id = :sid;'
        )
        await cursor.execute(query, {'id': rowid, 'sid': provider_id})

        await db.commit()

    return rowid
        

async def upload_artists(provider: Literal['spotify', 'youtube'], artists: Iterable) -> list[int]:
    async with (
        aiosqlite.connect('database/music.sqlite') as db,
        db.cursor() as cursor
    ):
        ids = []
        query = (
            f'INSERT INTO artists_ids (artist_name, {provider}_id) VALUES (:n, :pid) '
            f'ON CONFLICT DO UPDATE SET {provider}_id = :pid '
            'RETURNING rowid;'
        )
        for artist in artists:
            await cursor.execute(query, {'n': artist.name, 'pid': artist.id})
            ids.append((await cursor.fetchone())[0]) # type: ignore[non-null]

        await db.commit()
    return ids


async def dump(id: str, provider: Literal['spotify', 'youtube'], artists: Iterable, **data) -> int:
    results = await asyncio.gather(
        update_song(id, provider, **data),
        upload_artists(provider, artists)
    )

    async with (
        aiosqlite.connect('database/music.sqlite') as db,
        db.cursor() as cursor
    ):
        for artist_id in results[1]:
            await cursor.execute('INSERT OR IGNORE INTO song_authors VALUES (?, ?);', (results[0], artist_id))

        await db.commit()

    return results[0]



def get(id: int) -> list[tuple[str, int, str, str, str, str]]:
    with Connection() as cursor:
        query = (
            'SELECT song_title, album_id, artist_name, songs.duration, external_ids.spotify_id, artists_ids.spotify_id as sp_artist_id FROM songs '
            'INNER JOIN song_authors ON song_authors.song_id = songs.rowid '
            'INNER JOIN external_ids ON external_ids.song_id = songs.rowid '
            'INNER JOIN artists_ids ON song_authors.artist_id = artists_ids.rowid '
            'WHERE songs.rowid=?;'
        )
        cursor.execute(query, (id,))
        return cursor.fetchall()