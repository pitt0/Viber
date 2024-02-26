from typing import Iterable

from api import Connection
from api.utils import read_query
from models import Playlist
from resources import MISSING, Privacy
from resources.missing import Maybe
from typings import LocalID

__all__ = ("PlaylistsAPI",)


class PlaylistsAPI:

    @staticmethod
    async def get_playlist(
        *, playlist_id: LocalID = MISSING, title: str = MISSING, guild_id: int = MISSING
    ) -> Maybe[Playlist]:
        with Connection() as cursor:
            query = read_query("sql/playlists/get.sql")
            params = (playlist_id or None, title or None, guild_id or None)
            cursor.execute(query, params)

        if (data := cursor.fetchone()) is None:
            return Maybe(None)

        return Maybe(Playlist(*data))

    @staticmethod
    async def get_playlists(
        *, guild_id: int = MISSING, user_id: int = MISSING
    ) -> Maybe[Iterable[Playlist]]:
        assert not (guild_id is MISSING and user_id is MISSING)
        with Connection() as cursor:
            if guild_id is not MISSING:
                query = read_query("sql/playlists/get_from_guild.sql")
                params = (guild_id,)
            else:
                query = read_query("sql/playlists/get_from_author.sql")
                params = (user_id,)
            cursor.execute(query, params)

        if (data := cursor.fetchall()) == []:
            return Maybe(None)

        return Maybe(map(lambda p: Playlist(**p), data))

    @staticmethod
    async def rename(playlist_id: LocalID, name: str) -> None:
        with Connection() as cursor:
            cursor.execute(
                read_query("sql/playlists/update_title.sql"),
                (name, playlist_id),
            )

    @staticmethod
    async def set_privacy(playlist_id: LocalID, privacy: Privacy) -> None:
        with Connection() as cursor:
            cursor.execute(
                read_query("sql/playlists/update_privacy.sql"),
                (privacy.value, playlist_id),
            )

    @staticmethod
    async def delete_playlist(playlist_id: LocalID) -> None:
        with Connection() as cursor:
            cursor.execute(read_query("sql/playlists/delete.sql"), (playlist_id,))

    @staticmethod
    async def new(playlist_title: str, guild_id: int, user_id: int) -> None:
        with Connection() as cursor:
            cursor.execute(
                read_query("sql/playlists/create.sql"),
                (playlist_title, guild_id, user_id),
            )
