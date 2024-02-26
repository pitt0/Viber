import asyncio

from api import Connection
from api.cache import SongCache
from models import ExternalSong, LocalSong, Song
from typings import LocalID, NGExternalProvider

from .albums import AlbumsAPI
from .artists import ArtistsAPI
from .tracks import TracksAPI

__all__ = ("SongsAPI",)


class Links:

    @staticmethod
    def artists(song_id: LocalID) -> LocalID:
        with Connection() as cursor:
            cursor.execute(
                "SELECT artist_id FROM authors WHERE data_id = ?;", (song_id,)
            )
            return cursor.fetchone()[0]

    @staticmethod
    def album(song_id: LocalID) -> LocalID:
        with Connection() as cursor:
            cursor.execute("SELECT album_id FROM tracks WHERE song_id = ?;", (song_id,))
            return cursor.fetchone()[0]


class SongsAPI:

    @staticmethod
    async def get_song(
        track_id: LocalID, preferred_provider: NGExternalProvider = "spotify"
    ) -> LocalSong:
        # TODO: Test comment below
        # async with asyncio.TaskGroup() as tg:
        #     track = tg.create_task(TracksAPI.get_song(song_id, preferred_provider))
        #     album = tg.create_task(AlbumsAPI.get_album(Links.album(song_id), preferred_provider))
        #     artists = tg.create_task(ArtistsAPI.get_artists(Links.artists(song_id), preferred_provider))
        #     return Song(await track, await album, await artists, preferred_provider)
        return Song(
            *asyncio.gather(
                TracksAPI.get_track(track_id, preferred_provider),
                AlbumsAPI.get_album(Links.album(track_id), preferred_provider),
                ArtistsAPI.get_artists(Links.artists(track_id), preferred_provider),
            ),
            preferred_provider  # type: ignore
        )

    @staticmethod
    async def upload(song: ExternalSong, query: str | None = None) -> LocalSong:
        _song = Song(
            *asyncio.gather(
                TracksAPI.upload_track(song._track),
                AlbumsAPI.upload_album(song.album),
                ArtistsAPI.upload_artists(song.authors),
            ),
            song._provider  # type: ignore
        )
        if query:
            SongCache.add(query, _song.id)
        return _song
