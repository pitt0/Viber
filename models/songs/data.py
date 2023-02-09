from dataclasses import dataclass
from sqlite3 import Cursor
from typing import Any, Self

from resources import Connector
from resources import Time
from resources import SongBase


@dataclass
class SongData:

    id: str
    title: str
    author: str
    album: str
    thumbnail: str
    duration: str
    year: int

    spotify: str = ""
    youtube: str = ""

    source: str = ""

    db: bool = False # do not touch this, it is only used to check if this data has been taken from database

    def __eq__(self, __o: Self):
        return self.id == __o.id

    def __iter__(self):
        return (x for x in self.__dict__.values())

    def in_database(self, cur: Cursor) -> bool:
        """Looks if the song already is in the database.
        """
        if self.db:
            return True
        cur.execute("SELECT * FROM Songs WHERE ID=?;", (self.id,))
        return cur.fetchone() is not None

    def upload(self, cur: Cursor) -> None:
        """Uploads the whole song to the database.
        Does not cache.
        """
        cur.execute(f"""INSERT INTO Songs (ID, Title, Author, Album, Thumbnail, Duration, Year, Spotify, Youtube, Source) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
        (self.id, self.title, self.author, self.album, self.thumbnail, self.duration, self.year, self.spotify, self.youtube, self.source))

    def has_youtube(self, cur: Cursor) -> bool:
        """Looks through the database if the song has a youtube link associated.
        """
        if self.youtube == "":
            return True
        cur.execute("SELECT * FROM Songs WHERE ID=? AND Youtube=?;", (self.id, self.youtube))
        return cur.fetchone() is not None
    
    def has_spotify(self, cur: Cursor) -> bool:
        """Looks through the database if the song has a spotify link associated.
        """
        if self.spotify == "":
            return True
        cur.execute("SELECT * FROM Songs WHERE ID=? AND Spotify=?;", (self.id, self.spotify))
        return cur.fetchone() is not None

    def updateable(self, cur: Cursor) -> bool:
        """Looks through the database if there is any field that can be updated.
        """
        return not self.db and not (self.has_spotify(cur) and self.has_youtube(cur))

    def update(self, cur: Cursor):
        """Updates any field that can be updated in the database.
        """
        if self.youtube != "" and not self.has_youtube(cur):
            cur.execute("UPDATE Songs SET Youtube=?, Source=? WHERE ID=?;", (self.youtube, self.source, self.id))
        if self.spotify != "" and not self.has_spotify(cur):
            cur.execute("UPDATE Songs SET Spotify=? WHERE ID=?;", (self.spotify, self.id))


    @classmethod
    def from_id(cls, id: str) -> Self:
        """Creates a song starting from its id.
        """
        with Connector() as cur:
            cur.execute("SELECT * FROM Songs WHERE ID=?;", (id,))
            song: SongBase = cur.fetchone()
        self = cls(*song)
        self.db = True
        return self

    @classmethod
    def from_spotify(cls, data: dict[str, Any]) -> Self:
        """Creates a song starting from spotify data.
        """
        return cls(
            data["id"],
            data["name"],
            data["artists"][0]["name"],
            data["album"]["name"],
            data["album"]["images"][0]["url"],
            Time.from_ms(data["duration_ms"]),
            int(data["album"]["release_date"][:4]),
            data["external_urls"]["spotify"]
        )

    @classmethod
    def from_youtube(cls, data: dict[str, Any]) -> Self:
        """Creates a song starting from youtube data.
        """
        return cls(
            data["id"],
            data["title"],
            data["uploader"],
            data.get("album", "\u200b"),
            data["thumbnail"],
            data["duration_string"],
            data["upload_date"],
            "",
            data["original_url"],
            data["url"]
        )