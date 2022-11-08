from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing_extensions import Self

import discord

from ..utils import spotify as sp
from ..utils import youtube as yt

from .info import *

from connections import Connector, SongCache
from ..playlist import LikedSongs


if TYPE_CHECKING:
    from ..song import ChoosableSong


__all__ = ("Song",)

@dataclass
class Song:

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

    def __post_init__(self) -> None:
        self.url = self.spotify or self.youtube
        with Connector() as cur:
            cur.execute("SELECT * FROM Songs WHERE ID=? OR Youtube=?", (self.id, self.youtube))
            result = cur.fetchone()
            if result is None:
                self.upload()
                return
            if result[7] is None:
                self.update_info()

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Song) and __o.id == self.id

    def __ne__(self, __o: object) -> bool:
        return not self.__eq__(__o)

    @staticmethod
    def cached(reference: str) -> bool:
        with SongCache() as cache:
            return reference in cache

    def cache(self, reference: str) -> None:
        with SongCache() as cache:
            cache[reference] = self.id

    def upload(self) -> None:
        try:
            with Connector() as cur:
                cur.execute(f"""INSERT INTO Songs (ID, Title, Author, Album, Thumbnail, Duration, Year, Spotify, Youtube, Source) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                (self.id, self.title, self.author, self.album, self.thumbnail, self.duration, self.year, self.spotify, self.youtube, self.source))
        except Exception as e:
            print(e)

    def update_info(self) -> None:
        with Connector() as cur:
            cur.execute("""UPDATE Songs 
            SET Title=?, Author=?, Album=?, Thumbnail=?, Year=?, Spotify=? 
            WHERE Youtube=?;""",
            (self.id, self.title, self.author, self.album, self.thumbnail, self.year, self.spotify, self.youtube))

    def like(self, interaction: discord.Interaction) -> None:
        playlist = LikedSongs.from_database(interaction.user)
        playlist.add_song(self) # type: ignore

    @classmethod
    def from_id(cls, id: str) -> Self:
        with Connector() as cur:
            cur.execute(f"SELECT * FROM Songs WHERE ID=?;", (id,))
            song = cur.fetchone()
        return cls.from_database(song)

    @classmethod
    def from_database(cls, data: tuple[str | int, ...]) -> Self:
        info = DataInfo(*data)
        return cls(**info)

    @classmethod
    def from_choice(cls, choice: "ChoosableSong") -> Self:
        data = ChoiceInfo(choice)
        return cls(**data)

    @classmethod
    def from_cache(cls, reference: str) -> "Song":
        with SongCache() as cache:
            song_id = cache[reference]
        with Connector() as cur:
            cur.execute("SELECT * FROM Songs WHERE ID=?;", (song_id,))
            data = cur.fetchone()
        self = cls.from_database(data)
        return self
    
    @classmethod
    def from_reference(cls, reference: str) -> Self:
        if cls.cached(reference):
            return cls.from_cache(reference)

        info = sp.search(reference, limit=1)
        if len(info["tracks"]["items"]) > 0:
            track = info["tracks"]["items"][0]
            info = SpotifyInfo(**track)
            return cls(**info)
        else:
            result = yt.search_info(reference)
            info = YTInfo(**result)
            return cls(**info)

    @classmethod
    def from_spotify(cls, link: str):
        with Connector() as cur:
            cur.execute(f"SELECT * FROM Songs WHERE Spotify=?;", (link,))
            song = cur.fetchone()
            if song is not None:
                return cls.from_database(song)

        if "track" not in link:
            return None

        track = sp.track(link.split("/")[-1].split("?")[0])
        info = SpotifyInfo(**track)
        return cls(**info)

    @classmethod
    def from_youtube(cls, link: str):
        with Connector() as cur:
            cur.execute(f"SELECT * FROM Songs WHERE Youtube=?;", (link,))
            song = cur.fetchone()
            if song is not None:
                return cls.from_database(song)

        track = yt.from_link(link)
        info = YTInfo(**track)
        return cls(**info)