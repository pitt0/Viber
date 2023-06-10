from functools import cached_property
from typing import Self

import api.queries as queries
import datetime
import discord

from .paginator import Paginator
from .permissions import Owner, PermissionLevel
from models.songs import S
from resources import MISSING


__all__ = ('Base',)


class Base(Paginator[S]):

    __client: discord.Client

    def __init__(self, id: int, title: str, target: discord.User | discord.Guild, author: discord.User, creation_date: datetime.datetime, privacy: PermissionLevel) -> None:
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

    def empty_embed(self) -> discord.Embed:
        return super().empty_embed().set_author(name=f'Created by {self.author.display_name}', icon_url=self.author.display_avatar)

    def paginate(self, index: int) -> discord.Embed:
        _e = discord.Embed(
            title=self.title,
            description=f"by {self.author.display_name}",
            color=discord.Color.blurple()
        )
        _e.set_footer(text=f"Page {index} of {(len(self)//12)+1}")
        _e.set_author(name=f'Created by {self.author.display_name}', icon_url=self.author.display_avatar)

        return _e

    def embeds(self) -> list[discord.Embed]:
        return super().embeds(lambda song: song.as_field)


    async def dump(self, interaction: discord.Interaction) -> None:
        ...

    @classmethod
    async def load(cls, interaction: discord.Interaction, id: int = MISSING, title: str = MISSING, target_id: int = MISSING) -> Self:
        ...
    
    async def rename(self, name: str) -> None:
        self.title = name
        queries.write('update playlists set playlist_title = ? where rowid = ?;', (name, self.id))
    
    async def delete(self) -> None:
        queries.write('delete from playlists where rowid = ?;', (self.id,))
        queries.write('delete from playlist_songs where playlist_id = ?;', (self.id,))
        queries.write('delete from playlist_owners where playlist_id = ?;', (self.id,))

    async def owners(self) -> list[Owner]:
        data = queries.read('select owner_id, permission_lvl from playlist_owners where playlist_id = ?;', (self.id,))
        return [
            Owner(
                await self.__client.fetch_user(owner[0]),
                PermissionLevel(owner[1])
            )
            for owner in data
        ]
    
    async def add_song(self, song: S, by: int) -> None:
        self.append(song)
        queries.write('insert into playlist_songs (playlist_id, song_id, added_by) values (?, ?, ?);', (self.id, song.id, by))

    def remove_song(self, song: S) -> None:
        self.remove(song)
        queries.write('delete from playlist_songs where playlist_id = ? and song_id = ?;', (self.id, song.id))
