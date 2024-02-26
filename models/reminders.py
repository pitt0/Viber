import asyncio
import datetime

import dateutil.parser as dparser

__all__ = ("Reminder", "Timer")


class Timer:

    def __init__(
        self, playlist_id: str, weekday: int, remind_time: str, last_sent: str
    ) -> None:
        self.playlist_id = playlist_id
        self.weekday = weekday
        self.remind_at = dparser.parse(remind_time)
        self.last_sent = dparser.parse(last_sent)

    def next(self) -> datetime.datetime:
        if self.weekday == -1:
            delay = 1
        else:
            delay = (7 + self.weekday) - datetime.date.today().weekday()
        n = self.last_sent + datetime.timedelta(days=delay)

        return datetime.datetime(
            n.year, n.month, n.day, self.remind_at.hour, self.remind_at.minute
        )

    async def start(self) -> None:
        delay = (self.next() - datetime.datetime.now()).seconds
        await asyncio.sleep(delay)


class Reminder:

    def __init__(self, song_id: str, adviser_id: int, user_id: int) -> None:
        self.user_id = user_id
        self.song_id = song_id
        self.adviser_id = adviser_id
