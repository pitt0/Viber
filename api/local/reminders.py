import api.queries as queries
import dateutil.parser as dparser
import datetime
import discord
import random

from models import LocalSong
from resources import Connection, ReminderCache
from typing import Unpack


# type
ReminderEntry = tuple[int, int, str, str]
HEADERS = ['Hey [name], check this out!', "It's your lucky day!", 'Check out this song!', ]


class Reminder:

    _embed: discord.Embed # to be created in prepare
    _song: LocalSong

    def __init__(self, *entry: Unpack[ReminderEntry]) -> None:
        self.person_id: int = entry[0]
        self.weekday: int = entry[1]
        self.time: datetime.datetime = dparser.parse(entry[2]) # the time of the day at which user wants to recieve the notification
        self.last_remind: datetime.datetime = dparser.parse(entry[3])

    def next_remind(self) -> datetime.datetime:
        if self.weekday == -1:
            delay = 1
        else:
            delay = (7 + self.weekday) - datetime.date.today().weekday()
        n = self.last_remind + datetime.timedelta(days=delay)

        return datetime.datetime(n.year, n.month, n.day, self.time.hour, self.time.minute)

    def is_to_remind(self) -> bool:
        now = datetime.datetime.now()
        _next = self.next_remind()
        return (now >= _next and now.day != self.last_remind.day)

    @property
    def delay(self) -> int:
        return (self.next_remind() - datetime.datetime.now()).seconds
    
    def prepare(self) -> int:
        query = (
            "SELECT song_id, added_by FROM playlist_songs "
            "LEFT JOIN playlists ON playlists.rowid = playlist_songs.playlist_id "
            "WHERE playlist_title = 'Advices' AND target_id = ?;"
        )
        songs_ids: list[tuple[int, int]] = queries.read(query, (self.person_id,))
        cache = ReminderCache.load(self.person_id)
        if len(cache) > len(songs_ids):
            ReminderCache.delete_first(self.person_id)
        
        while (choice := random.choice(songs_ids)) in cache:
            continue

        self._song = LocalSong.load(choice[0])

        self._embed = discord.Embed(
            title=random.choice(HEADERS),
            description=self._song,
            color=discord.Colour.orange()
        )
        self._embed.set_image(url=self._song.thumbnail)
        return choice[1] # returns advicer's id, to be added as author
    
    def embed(self, user: discord.User, adviser: discord.User) -> discord.Embed:
        self._embed.title = self._embed.title.replace('[name]', user.display_name) # type: ignore[non-null]
        self._embed.set_footer(text=f"Advised by {adviser.display_name}", icon_url=adviser.display_avatar)
        return self._embed
    
    def sent(self) -> None:
        now = datetime.datetime.now()
        self.last_remind = now
        queries.write("UPDATE reminders SET last_sent = CURRENT_DATE WHERE person_id = ?", (self.person_id,))
        ReminderCache.add(self.person_id, self._song.id)




def get() -> list[Reminder]:
    with Connection() as cursor:
        query = (
            "SELECT reminders.person_id, reminders.weekday, remind_time, last_sent FROM reminders "
            "LEFT JOIN playlists ON playlists.target_id = reminders.person_id AND playlist_title = 'Advices' "
            "INNER JOIN playlist_songs ON playlists.rowid = playlist_songs.playlist_id "
            "WHERE reminders.active = 1;"
        )
        cursor.execute(query)
        data: list[ReminderEntry] = cursor.fetchall()

    return [Reminder(*entry) for entry in set(data)]

    