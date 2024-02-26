from sqlite3 import Cursor
from typing import Sequence

from api import Connection
from models import Artist, ExternalArtist
from typings import LocalID, NGExternalProvider

from .base import _API

__all__ = ("ArtistsAPI",)


class ArtistsAPI(_API, table="artists"):

    @classmethod
    async def get_artists(
        cls, artists_ids: Sequence[LocalID], provider: NGExternalProvider = "spotify"
    ) -> Sequence[Artist]:
        artists_data = await cls._get_raw_data(
            f"artist_name, {provider}_id",
            artists_ids,
            pool=f"({', '.join(['?'] * len(artists_ids))})",
        )
        return [Artist(*artist, provider) for artist in artists_data]  # type: ignore

    @staticmethod
    def _get_id(cursor: Cursor, artist: str) -> LocalID:
        cursor.execute(
            "SELECT artist_id FROM artists WHERE artist_name = ?;", (artist,)
        )
        return cursor.fetchone()

    @classmethod
    def get_id(cls, artist: str) -> LocalID:
        with Connection() as cursor:
            return cls._get_id(cursor, artist)

    @classmethod
    async def upload_artists(
        cls, artists: Sequence[ExternalArtist]
    ) -> Sequence[Artist]:
        with Connection() as cursor:
            ids = []
            query = "INSERT OR IGNORE INTO artists (artist_name) VALUES (?);"
            for artist in artists:
                # Insert artist
                cursor.execute(query, (artist.name,))

                # Get id
                ids.append(cls._get_id(cursor, artist.name))

                # Update external id
                super()._update_provider_id(cursor, artist.provider, ids[-1], artist.id)

        return await cls.get_artists(ids)
