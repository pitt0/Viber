from functools import cached_property
from typing import Self

import datetime
import discord

from .paginator import Paginator
from .permissions import Owner, PlaylistPermission
from models.requests import PlaylistRequest
from models.songs import S
from resources import MISSING


__all__ = ('Base',)


class Base(list[S], Paginator):

    __client: discord.Client

    def __init__(self, id: int, title: str, target: discord.User | discord.Guild, author: discord.User, creation_date: datetime.datetime, privacy: PlaylistPermission) -> None:
        self.id = id
        self.title = title
        self.target = target
        self.author = author
        self.creation_date = creation_date
        self.privacy = privacy


    @cached_property
    def date(self) -> str:
        return self.creation_date.strftime('%d/%m/%y')

    @cached_property
    def upload_date(self) -> str:
        return self.creation_date.strftime('%y-%m-%d %H:%M:%S')

    def paginate(self, index: int) -> discord.Embed:
        _e = discord.Embed(
            title=self.title,
            description=f"by {self.author.display_name}",
            color=discord.Color.blurple()
        )
        _e.set_footer(text=f"Page {index}")

        for song in self[(index - 1) * 12 : index*12]:
            _e.add_field(**song.as_field)
        return _e

    def embeds(self) -> list[discord.Embed]:
        return super().embeds(lambda song: song.as_field)


    async def dump(self) -> None:
        ...

    @classmethod
    async def load(cls, interaction: discord.Interaction, id: int = MISSING, title: str = MISSING, target_id: int = MISSING) -> Self:
        ...
    
    @property
    async def owners(self) -> list[Owner]:
        data = PlaylistRequest.owners(self.id)
        return [
            Owner(
                await self.__client.fetch_user(owner[0]),
                PlaylistPermission(owner[1])
            )
            for owner in data
        ]
    
    def add_song(self, song: S, by: int) -> None:
        self.append(song)
        PlaylistRequest.add(self.id, song.id, by)

    def remove_song(self, song: S) -> None:
        self.remove(song)
        PlaylistRequest.remove(self.id, song.id)
