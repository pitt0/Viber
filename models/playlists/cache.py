from dataclasses import dataclass
from typing import Self

import discord

from resources import Connector


__all__ = ("CachedPlaylist",)


@dataclass
class CachedPlaylist:
    name: str
    guild: int
    author: int

    @classmethod
    def load(cls) -> list[Self]:
        cache = []
        with Connector() as cur:
            cur.execute("SELECT Title, Author, Keyword FROM Playlists;")
            cache = [cls(*playlist) for playlist in cur.fetchall()]
        return cache

    def __guild_scope(self, interaction: discord.Interaction) -> bool:
        return interaction.guild == None or interaction.guild.id == self.guild
    
    def showable(self, interaction: discord.Interaction) -> bool:
        return self.__guild_scope(interaction) and interaction.user.id == self.author
    
    def is_input(self, query: str) -> bool:
        return query.lower() in self.name.lower()