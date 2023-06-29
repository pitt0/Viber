import aiosqlite
import asyncio
from resources.connections import Connection
from typing import Literal, Iterable


AlbumLocalId = int
ArtistLocalId = int
AlbumData = tuple[AlbumLocalId, str, str, str, str, str, str]


async def upload_album(provider_id: str, provider: Literal['spotify', 'youtube'], **data) -> AlbumLocalId:
    async with (
        aiosqlite.connect('database/music.sqlite') as db,
        db.cursor() as cursor
    ):
        query = (
            'INSERT INTO albums VALUES (:name, :release_date, :thumbnail) '
            'ON CONFLICT DO UPDATE SET thumbnail = :thumbnail RETURNING rowid;'
        )
        await cursor.execute(query, data)
        rowid = (await cursor.fetchone())[0] # type: ignore[non-null]

        query = (
            f'INSERT INTO external_album_ids (album_id, {provider}_id) VALUES (:id, :pid) '
            f'ON CONFLICT DO UPDATE SET {provider}_id = :pid;'
        )
        await cursor.execute(query, {'id': rowid, 'pid': provider_id})

        await db.commit()
    return rowid


async def upload_artists(provider: Literal['spotify', 'youtube'], artists: Iterable) -> list[ArtistLocalId]:
    async with (
        aiosqlite.connect('database/music.sqlite') as db,
        db.cursor() as cursor
    ):
        ids = []
        query = (
            f'INSERT INTO artists_ids (artist_name, {provider}_id) VALUES (:n, :pid) '
            f'ON CONFLICT DO UPDATE SET {provider}_id = :pid RETURNING rowid;'
        )
        for artist in artists:
            params = {'n': artist.name, 'pid': artist.id}
            
            await cursor.execute(query, params)
            ids.append((await cursor.fetchone())[0]) # type: ignore[non-null]

        await db.commit()
    return ids


async def dump(id: str, provider: Literal['spotify', 'youtube'], artists: Iterable, **data) -> int:
    results = await asyncio.gather(
        upload_album(id, provider, **data),
        upload_artists(provider, artists)
    )

    async with (
        aiosqlite.connect('database/music.sqlite') as db,
        db.cursor() as cursor
    ):
        for artist_id in results[1]:
            await cursor.execute(('INSERT OR IGNORE INTO album_authors VALUES (?, ?);'), (results[0], artist_id))

        await db.commit()
    return results[0]



def get(id: int) -> list[AlbumData]:
    with Connection() as cursor:
        query = (
            'SELECT albums.rowid, album_name, artist_name, release_date, thumbnail, aext.spotify_id, artists_ids.spotify_id as sp_artist_id FROM albums '
            'INNER JOIN external_album_ids AS aext ON aext.album_id = albums.rowid '
            'INNER JOIN album_authors ON album_authors.album_id = albums.rowid '
            'INNER JOIN artists_ids ON album_authors.artist_id = artists_ids.rowid '
            'WHERE albums.rowid = ?;'
        )
        cursor.execute(query, (id,))
        return cursor.fetchall()