from sqlite3 import Cursor
from typing import Any
from typing_extensions import Self

import discord

from .data import SongData
from models.utils import spotify as sp
from models.utils import youtube as yt
from models.utils import WrongLink
from resources import Connector, SongCache


class Song:

    data: SongData

    embed: discord.Embed

    source: str
    url: str


    def __init__(self, data: SongData, upload: bool = True):
        self.data = data

        self.embed = discord.Embed(
            title=data.title,
            description=f"{data.author} • {data.album}",
            color=discord.Colour.dark_purple()
        ).set_thumbnail(url=data.thumbnail)
        self.embed.add_field(name="Duration", value=data.duration, inline=True)
        self.embed.add_field(name="Year", value=data.year, inline=True)


        self.source = data.source
        self.url = data.spotify or data.youtube

        if upload:
            with Connector() as cur:
                if not self.exists(cur):
                    self.upload(cur)
                elif self.updateable(cur):
                    self.update(cur)

    
    @property
    def field(self):
        return {"name": self.data.title, "value": f"{self.data.author} • {self.data.album}", "inline": True}
    
    
    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, SongData):
            return self.data == __o
        elif isinstance(__o, tuple):
            return all(data == __o[i] for i, data in enumerate(self.data))
        return isinstance(__o, self.__class__) and __o.data == self.data

    def __ne__(self, __o: object) -> bool:
        return not self.__eq__(__o)

    def __str__(self) -> str:
        return f"{self.data.title} by {self.data.author}"

    
    def exists(self, cur: Cursor) -> bool:
        return self.data.in_database(cur)

    def upload(self, cur: Cursor) -> None:
        try:
            self.data.upload(cur)
        except Exception as e:
            print(e)

    def updateable(self, cur: Cursor) -> bool:
        return self.data.updateable(cur)

    def update(self, cur: Cursor) -> None:
        try:
            self.data.update(cur)
        except Exception as e:
            print(e)

    @staticmethod
    def cached(reference: str):
        with SongCache() as cache:
            return reference in cache

    def cache(self, reference: str):
        with SongCache() as cache:
            cache[reference] = self.data.id

    
    @classmethod
    def search(cls, reference: str):
        if "open.spotify.com" in reference:
            self = cls.from_spotify(reference)
            if self is None:
                raise WrongLink(f"(This link)[{reference}] returned no result.")
        
        elif "youtu.be" in reference or "youtube.com" in reference:
            self = cls.from_youtube(reference)
        
        else:
            self = cls.from_reference(reference)

        self.cache(reference)
        return self

    
    @classmethod
    def from_id(cls, id: str) -> Self:
        return cls(SongData.from_id(id))
    
    @classmethod
    def from_reference(cls, reference: str) -> Self:
        # Check from cache
        with SongCache() as cache:
            if reference in cache:
                return cls.from_id(cache[reference])
        
        # Check from somewhere else
        data = sp.search(reference, limit=1)
        if len(data) > 0:
            return cls(SongData.from_spotify(data[0]))
        else:
            data = yt.search_info(reference)
            return cls(SongData.from_youtube(data))

    @classmethod
    def from_spotify(cls, link: str) -> Self | None:
        with Connector() as cur:
            cur.execute(f"SELECT * FROM Songs WHERE Spotify=?;", (link,))
            song = cur.fetchone()
            if song is not None:
                return cls(SongData(*song))

        if "track" not in link:
            return None

        track = sp.track(link.split("/")[-1].split("?")[0])
        return cls(SongData.from_spotify(track))

    @classmethod
    def from_youtube(cls, link: str) -> Self:
        with Connector() as cur:
            cur.execute(f"SELECT * FROM Songs WHERE Youtube=?;", (link,))
            song = cur.fetchone()
            if song is not None:
                return cls(SongData(*song))

        track = yt.from_link(link)
        return cls(SongData.from_youtube(track))

    @classmethod
    def as_choice(cls, s_data: dict[str, Any] | None = None, y_data: dict[str, Any] | None = None) -> Self:
        if s_data is None:
            return cls(SongData.from_youtube(y_data), False) # type: ignore
        else:
            return cls(SongData.from_spotify(s_data), False)
