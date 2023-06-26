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
            'insert into songs values (:title, :album_id, :duration) '
            'on conflict do update set duration = :duration ' # HACK forced update so it returns rowid
            'returning rowid;'
        )
        await cursor.execute(query, data)
        rowid = (await cursor.fetchone())[0] # type: ignore[non-null]
        
        query = (
            f'insert into external_ids (song_id, {provider}_id) values (:id, :sid) '
            f'on conflict do update set {provider}_id = :sid;'
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
            f'insert into artists_ids (artist_name, {provider}_id) values (:n, :pid) '
            f'on conflict do update set {provider}_id = :pid '
            'returning rowid;'
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
            await cursor.execute('insert or ignore into song_authors values (?, ?);', (results[0], artist_id))

        await db.commit()

    return results[0]



def get(id: int) -> list[tuple[str, int, str, str, str, str]]:
    with Connection() as cursor:
        query = (
            'select song_title, album_id, artist_name, songs.duration, external_ids.spotify_id, artists_ids.spotify_id as sp_artist_id '
            'from songs inner join song_authors on song_authors.song_id = songs.rowid '
            'inner join external_ids on external_ids.song_id = songs.rowid '
            'inner join artists_ids on song_authors.artist_id = artists_ids.rowid '
            'where songs.rowid=?;'
        )
        cursor.execute(query, (id,))
        return cursor.fetchall()