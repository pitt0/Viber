from abc import abstractclassmethod
from dataclasses import dataclass
from typing import Self

import discord

from resources import Connector, USER


__all__ = (
    "GuildPlaylist",
    "UserPlaylist"
)


@dataclass
class EmbedPlaylist:
    title: str
    date: str

    @abstractclassmethod
    def load(cls, x: ...) -> list[Self]:
        """Loads the playlist from database.
        """
        ...

    @staticmethod
    def paginate(title: str, playlists: list) -> list[discord.Embed]:
        es: list[discord.Embed] = []
        
        for index, playlist in enumerate(playlists):
            page = (index // 12) + 1

            if page > len(es):
                es.append(
                    discord.Embed(
                        title=title,
                        description=f"Page {page}"
                    )
                )
            
            current = es[-1] # latest created embed
            current.add_field(name=playlist.title, value=playlist.date, inline=True)
        
        return es



@dataclass
class GuildPlaylist(EmbedPlaylist):

    author: str

    @classmethod
    def load(cls, guild: discord.Guild) -> list[Self]:
        with Connector() as cur:
            cur.execute("SELECT Title, Date, Author FROM Playlists WHERE Guild=? AND Locked=0;", (guild.id,))
            return [cls(*playlist) for playlist in cur.fetchall()]

    @classmethod
    def embed(cls, guild: discord.Guild) -> list[discord.Embed]:
        playlists = cls.load(guild)
        return cls.paginate(f"{guild.name}'s Playlists", playlists)

@dataclass
class UserPlaylist(EmbedPlaylist):
    
    @classmethod
    def load(cls, user: USER) -> list[Self]:
        with Connector() as cur:
            cur.execute("SELECT Title, Date FROM Playlists WHERE Author=?;", (user.id,))
            return [cls(*playlist) for playlist in cur.fetchall()]

    @classmethod
    def embeds(cls, user: USER) -> list[discord.Embed]:
        playlists = cls.load(user)
        return cls.paginate(f"{user.display_name}'s Playlists", playlists)

