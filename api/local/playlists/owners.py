from typing import Optional

from api import Connection
from api.utils import read_query
from resources import PermissionLevel
from typings import LocalID

__all__ = ("PlaylistOwnersAPI",)


class PlaylistOwnersAPI:

    @staticmethod
    async def get_owners(playlist_id: LocalID) -> dict[int, PermissionLevel]:
        with Connection() as cursor:
            query = read_query("sql/playlist_owners/get.sql")
            cursor.execute(query, (playlist_id,))
        return {user_id: PermissionLevel(p_lvl) for user_id, p_lvl in cursor.fetchall()}

    @staticmethod
    async def get_owner_level(playlist_id: LocalID, user_id: int) -> PermissionLevel:
        with Connection() as cursor:
            query = read_query("sql/playlist_owners/level.sql")
            cursor.execute(query, (playlist_id, user_id))
            levels: Optional[tuple[int, int]] = cursor.fetchone()
            if levels is None:
                return PermissionLevel.Extern

        return PermissionLevel(max(levels))

    @staticmethod
    async def add_owner(
        playlist_id: LocalID, user_id: int, permission_level: PermissionLevel
    ) -> None:
        with Connection() as cursor:
            query = read_query("sql/playlist_owners/add.sql")
            cursor.execute(
                query,
                (playlist_id, user_id, permission_level.value, permission_level.value),
            )

    @staticmethod
    async def update_owner(
        playlist_id: LocalID, user_id: int, permission_level: PermissionLevel
    ) -> None:
        with Connection() as cursor:
            cursor.execute(
                read_query("sql/playlist_owners/update.sql"),
                (permission_level.value, playlist_id, user_id),
            )

    @staticmethod
    async def remove_owner(playlist_id: LocalID, user_id: int) -> None:
        with Connection() as cursor:
            cursor.execute(
                read_query("sql/playlist_owners/remove.sql"),
                (playlist_id, user_id),
            )
