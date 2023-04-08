from typing import Self

import datetime
import dateutil.parser as dparser
import discord

from .permissions import PlaylistPermission
from .base import Base
from models.songs import LocalSong
from resources.typings import MISSING
from resources.requests import PlaylistRequest


__all__ = ('LocalPlaylist',)


class LocalPlaylist(Base[LocalSong]):

    @classmethod
    async def load(cls, interaction: discord.Interaction, id: int = MISSING, title: str = MISSING, target_id: int = MISSING):
        data = PlaylistRequest.get(id, title, target_id)
        try:
            target = await interaction.client.fetch_guild(data[2])
        except:
            target = await interaction.client.fetch_user(data[2])
        user = await interaction.client.fetch_user(data[3])
        self = cls(data[0], data[1], target, user, dparser.parse(data[4], yearfirst=True), PlaylistPermission(data[5]))

        songs = PlaylistRequest.songs(id)
        for song in songs:
            # NOTE: if this is too slow, make SongPreview class that only uses title, author etc.
            self.append(LocalSong.load(song[0]))

        self.__client = interaction.client
        return self
    
    @classmethod
    def create(cls, name: str, interaction: discord.Interaction, privacy: PlaylistPermission) -> Self:
        target = interaction.guild or interaction.user
        rowid = PlaylistRequest.dump(name, target.id, interaction.user.id, privacy.value)
        return cls(rowid, name, target, interaction.user, datetime.datetime.today(), privacy) # type: ignore