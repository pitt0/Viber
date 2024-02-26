from typing import Iterable

from api import Connection
from api.local.base import _API
from api.local.songs import SongsAPI
from api.utils import read_query
from models import LocalSong
from typings import LocalID

__all__ = ("PlaylistSongsAPI",)


class PlaylistSongsAPI(_API):

    @staticmethod
    async def get_songs(playlist_id: LocalID) -> Iterable[LocalSong]:
        with Connection() as cursor:
            cursor.execute(
                read_query("sql/playlist_songs/get.sql"),
                (playlist_id,),
            )
        return map(lambda s: await SongsAPI.get_song(s), cursor.fetchall())

    @staticmethod
    async def is_present(playlist_id: LocalID, song_id: LocalID) -> bool:
        with Connection() as cursor:
            cursor.execute(
                read_query("sql/playlist_songs/exists.sql"),
                (playlist_id, song_id),
            )
        return bool(cursor.fetchone())

    @staticmethod
    async def add_song(playlist_id: LocalID, song_id: LocalID, user_id: int) -> None:
        with Connection() as cursor:
            cursor.execute(
                read_query("sql/playlist_songs/add.sql"),
                (playlist_id, song_id, user_id),
            )

    @staticmethod
    async def remove_song(playlist_id: LocalID, song_id: LocalID) -> None:
        with Connection() as cursor:
            cursor.execute(
                read_query("sql/playlist_songs/remove.sql"),
                (playlist_id, song_id),
            )
