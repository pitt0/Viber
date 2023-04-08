from abc import abstractclassmethod
from dataclasses import dataclass
from typing import Self

import discord

from .paginator import Paginator
from models.utils import USER
from resources import Connection


__all__ = (
    "GuildLister",
    "UserLister"
)


@dataclass
class EmbedPlaylist:
    title: str
    date: str


class Lister(list[EmbedPlaylist], Paginator):

    def __init__(self, title: str, *playlists) -> None:
        super().__init__(playlists)
        self.title = title

    @abstractclassmethod
    def load(cls) -> Self:
        """Loads the playlist from database.
        """
        ...

    @staticmethod
    def paginate(title: str, playlists: list) -> list[discord.Embed]:
        pages: list[discord.Embed] = []

        for index, playlist in enumerate(playlists):
            page = (index // 12) + 1

            if page > len(pages):
                pages.append(
                    discord.Embed(
                        title=title,
                        description=f"Page {page}"
                    )
                )

            pages[-1].add_field(name=playlist.title, value=playlist.date, inline=True)

        return pages
    
    def embeds(self) -> list[discord.Embed]:
        return super().embeds(lambda playlist: {'name': playlist.title, 'value': playlist.date, 'inline': True})



class GuildLister(Lister):

    @classmethod
    def load(cls, guild: discord.Guild) -> Self:
        with Connection() as cur:
            query = (
                'select playlist_title, creation_date ' # NOTE: there was author_id
                'from playlists '
                'where target_id = ? and privacy > 0 and author_id != 824230778187415552;'
            )
            cur.execute(query, (guild.id,))
            return cls(
                f"{guild.name}'s Playlists", 
                (EmbedPlaylist(*playlist) for playlist in cur.fetchall())
            )


    def embeds(self, guild: discord.Guild) -> list[discord.Embed]:
        self = self.load(guild)
        return super().embeds()


class UserLister(Lister):
    
    @classmethod
    def load(cls, user: USER, show_private: bool = False) -> Self:
        with Connection() as cur:
            query = (
                'select playlist_title, creation_date, privacy '
                'from playlists '
                'where author_id = ?;'
            )
            cur.execute(query, (user.id,))
            
            return cls(
                f"{user.display_name}'s Playlists",
                (
                    EmbedPlaylist(*playlist) 
                    for playlist in cur.fetchall() 
                    if show_private or playlist[2] > 0
                )
            )

    def embeds(self, user: USER) -> list[discord.Embed]:
        self = self.load(user)
        return super().embeds()

