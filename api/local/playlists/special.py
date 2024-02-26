from api import Connection
from models import LocalSong
from typings import LocalID, UserID

from .songs import SongsAPI

__all__ = ("AdvicesAPI", "FavouritesAPI")


class AdvicesAPI:

    @staticmethod
    async def get_playlist_id(user_id: UserID) -> LocalID | None:
        with Connection() as cursor:
            query = "SELECT playlist_id FROM special WHERE user_id = ? AND playlist_type = ?;"
            cursor.execute(query, (user_id, "Advices"))
        return (cursor.fetchone() or [None])[0]

    @staticmethod
    async def get_advices(user_id: UserID) -> list[LocalSong]:
        with Connection() as cursor:
            query = (
                "SELECT song_id FROM special "
                "JOIN playlist_songs ON special.playlist_id = playlist_songs.playlist_id "
                "WHERE user_id = ? AND playlist_type = 'Advices';"
            )
            cursor.execute(query, (user_id,))

        return [await SongsAPI.get_song(track_id) for track_id, in cursor.fetchall()]

    @staticmethod
    async def add_song(user_id: UserID, song_id: LocalID, adviser_id: UserID) -> None:
        with Connection() as cursor:
            cursor.execute(
                "INSERT OR IGNORE INTO special (playlist_type, user_id) VALUES (?, ?);",
                ("Advices", user_id),
            )
            cursor.execute(
                "SELECT playlist_id FROM special WHERE playlist_type = 'Advices' AND user_id = ?;",
                (user_id,),
            )
            (playlist_id,) = cursor.fetchone()
            cursor.execute(
                "INSERT INTO playlist_songs (playlist_id, song_id, added_by) VALUES (?, ?, ?);",
                (playlist_id, song_id, adviser_id),
            )

    @classmethod
    async def remove_song(cls, user_id: UserID, song_id: LocalID) -> None:
        playlist_id = await cls.get_playlist_id(user_id)
        with Connection() as cursor:
            cursor.execute(
                "DELETE FROM playlist_songs WHERE playlist_id = ? and song_id = ?;",
                (playlist_id, song_id),
            )


class FavouritesAPI:

    @staticmethod
    async def get_playlist_id(user_id: UserID) -> LocalID | None:
        with Connection() as cursor:
            query = "SELECT playlist_id FROM special WHERE user_id = ? AND playlist_type = ?;"
            cursor.execute(query, (user_id, "Favourites"))
        return (cursor.fetchone() or [None])[0]

    @staticmethod
    async def get_favourites(user_id: UserID) -> list[LocalSong]:
        with Connection() as cursor:
            query = (
                "SELECT song_id FROM special "
                "JOIN playlist_songs ON special.playlist_id = playlist_songs.playlist_id "
                "WHERE user_id = ? AND playlist_type = 'Favourites';"
            )
            cursor.execute(query, (user_id,))

        return [await SongsAPI.get_song(track_id) for track_id, in cursor.fetchall()]

    @staticmethod
    async def add_song(user_id: UserID, song_id: LocalID) -> None:
        with Connection() as cursor:
            cursor.execute(
                "INSERT OR IGNORE INTO special (playlist_type, user_id) VALUES (?, ?);",
                ("Favourites", user_id),
            )
            cursor.execute(
                "SELECT playlist_id FROM special WHERE playlist_type = 'Favourites' AND user_id = ?;",
                (user_id,),
            )
            (playlist_id,) = cursor.fetchone()
            cursor.execute(
                "INSERT INTO playlist_songs (playlist_id, song_id, added_by) VALUES (?, ?, ?);",
                (playlist_id, song_id, user_id),
            )

    @classmethod
    async def remove_song(cls, user_id: UserID, song_id: LocalID) -> None:
        playlist_id = await cls.get_playlist_id(user_id)
        with Connection() as cursor:
            cursor.execute(
                "DELETE FROM playlist_songs WHERE playlist_id = ? and song_id = ?;",
                (playlist_id, song_id),
            )
