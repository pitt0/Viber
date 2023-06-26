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
            'insert into albums values (:name, :release_date, :thumbnail) '
            'on conflict do update set thumbnail = :thumbnail returning rowid;'
        )
        await cursor.execute(query, data)
        rowid = (await cursor.fetchone())[0] # type: ignore[non-null]

        query = (
            f'insert into external_album_ids (album_id, {provider}_id) values (:id, :pid) '
            f'on conflict do update set {provider}_id = :pid;'
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
            f'insert into artists_ids (artist_name, {provider}_id) values (:n, :pid) '
            f'on conflict do update set {provider}_id = :pid returning rowid;'
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
            await cursor.execute(('insert or ignore into album_authors values (?, ?);'), (results[0], artist_id))

        await db.commit()
    return results[0]



def get(id: int) -> list[AlbumData]:
    with Connection() as cursor:
        query = (
            'select albums.rowid, album_name, artist_name, release_date, thumbnail, aext.spotify_id, artists_ids.spotify_id as sp_artist_id '
            'from albums '
            'inner join external_album_ids as aext on aext.album_id = albums.rowid '
            'inner join album_authors on album_authors.album_id = albums.rowid '
            'inner join artists_ids on album_authors.artist_id = artists_ids.rowid '
            'where albums.rowid = ?;'
        )
        cursor.execute(query, (id,))
        return cursor.fetchall()