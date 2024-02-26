import random

from api import Connection
from api.cache import ReminderCache
from models import Reminder, Timer

from .base import _API

__all__ = ("ReminderAPI",)


class ReminderAPI(_API):

    @staticmethod
    async def check_active(user_id: int) -> bool | None:
        with Connection() as cursor:
            query = "SELECT active FROM reminders WHERE user_id = ?;"
            cursor.execute(query, (user_id,))
            if (result := cursor.fetchone()) is None:
                # user is not registered
                return None
            return bool(result)

    @staticmethod
    async def get_reminder(playlist_id: str) -> Reminder:
        with Connection() as cursor:
            query = (
                "SELECT song_id, added_by, user_id FROM special "
                "JOIN playlist_songs ON playlist_songs.playlist_id = special.playlist_id "
                "WHERE playlist_id = ?;"
            )
            cursor.execute(query, (playlist_id,))
            results = cursor.fetchall()

        user_id = results[0][2]
        while len(ReminderCache.load(user_id)) > len(results) // 2:
            ReminderCache.remove_first(user_id)

        cache = ReminderCache.load(user_id)
        while (choice := random.choice(results))[0] in cache:
            continue

        return Reminder(*choice)

    @staticmethod
    async def get_timers() -> list[Timer]:
        with Connection() as cursor:
            cursor.execute(
                "SELECT playlist_id, weekday, remind_time, last_sent FROM reminders WHERE active = 1;"
            )
            return [Timer(*data) for data in cursor.fetchall()]
