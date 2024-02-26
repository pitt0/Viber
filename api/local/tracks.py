from sqlite3 import Cursor

from api import Connection
from api.cache import SongCache
from api.utils import DataSearch
from models import ExternalTrack, Track
from typings import LocalID, NGExternalProvider

from .base import _API

__all__ = ("TracksAPI",)


class TracksAPI(_API, table="songs"):

    @classmethod
    async def get_track(
        cls, track_id: LocalID, provider: NGExternalProvider = "spotify"
    ) -> Track:
        track_data = await cls._get_raw_data(
            f"song_id, song_title, duration_string, {provider}_id", (track_id,)
        )
        return Track(*track_data, provider)  # type: ignore

    @staticmethod
    def _get_id(cursor: Cursor, track: ExternalTrack) -> list[tuple[LocalID]]:
        cursor.execute(
            "SELECT song_id FROM songs WHERE song_title = ? AND song_duration = ?;",
            (track.title, track.duration),
        )
        return cursor.fetchall()

    @classmethod
    def _is_present(cls, cursor: Cursor, track: ExternalTrack) -> DataSearch:
        found_empty = False

        registered = cls._get_id(cursor, track)

        if not registered:
            # the queue is empty
            return DataSearch.NotFound

        for track_id in registered:
            cursor.execute(
                f"SELECT {track.provider}_id FROM data WHERE data_id = ?;", track_id
            )
            (ext_id,) = cursor.fetchone()

            if ext_id is None:
                found_empty = True
                continue

            if ext_id == track.id:
                return DataSearch.Found

        if found_empty:
            # there is at least one data entry that has only data_id
            return DataSearch.DataEmpty

        return DataSearch.FoundName

    @classmethod
    def is_present(cls, track: ExternalTrack) -> DataSearch:
        with Connection() as cursor:
            return cls._is_present(cursor, track)

    @classmethod
    async def upload_track(cls, track: ExternalTrack) -> Track:
        with Connection() as cursor:

            match cls._is_present(cursor, track):
                case DataSearch.NotFound:
                    # insert into database
                    query = "INSERT INTO songs (song_title, duration) VALUES (?, ?);"
                    cursor.execute(query, (track.title, track.duration))
                    # retrieve song_id
                    query = "SELECT song_id FROM songs WHERE song_title = ?;"
                    cursor.execute(query, (track.title,))
                    (track_id,) = cursor.fetchone()
                    # update data table
                    cls._update_provider_id(cursor, track.provider, track_id, track.id)
                    # upload cache
                    if track.reference:
                        SongCache.add(track.reference, track_id)

                case DataSearch.DataEmpty:
                    # TODO: Implement
                    raise NotImplementedError

                case DataSearch.FoundName:
                    # check the number of songs in the database
                    query = "SELECT COUNT(*) FROM songs;"
                    cursor.execute(query)
                    (n,) = cursor.fetchone()
                    # insert into database specifing song_id
                    track_id = f"s{n+1}"
                    query = "INSERT INTO songs VALUES (?, ?, ?);"
                    cursor.execute(query, (track_id, track.title, track.duration))
                    # update data table
                    cls._update_provider_id(cursor, track.provider, track_id, track.id)

                case DataSearch.Found:
                    track_id = cls._get_local_id(cursor, track.provider, track.id)
                    assert (
                        track_id is not None
                    ), "`_is_present` returned `DataSearch.Found`, but local_id is `None`"

        return await cls.get_track(track_id, track.provider)
