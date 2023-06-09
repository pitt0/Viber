from typing import Self

import datetime
import dateutil.parser as dparser
import discord
import api.local.playlist as queries

from .permissions import PermissionLevel
from .base import Base
from api.local.playlist import get, dump
from models.songs import LocalSong
from resources.types import MISSING


__all__ = ('LocalPlaylist',)


class LocalPlaylist(Base[LocalSong]):

    @classmethod
    async def load(cls, interaction: discord.Interaction, id: int = MISSING, title: str = MISSING, target_id: int = MISSING) -> Self:
        data = get(id, title, target_id)
        try:
            target = await interaction.client.fetch_guild(data[2])
        except discord.NotFound:
            target = await interaction.client.fetch_user(data[2])
        user = await interaction.client.fetch_user(data[3])
        self = cls(data[0], data[1], target, user, dparser.parse(data[4], yearfirst=True), PermissionLevel(data[5]))

        songs = queries.songs(self.id)
        for song in songs:
            song = LocalSong.load(song[0])
            self.append(song)

        self.__client = interaction.client
        return self

    @classmethod
    def create(cls, name: str, interaction: discord.Interaction, privacy: PermissionLevel) -> Self:
        target = interaction.guild or interaction.user
        rowid = dump('', 'local', name, target.id, interaction.user.id, privacy.value) # HACK: provider_id set as ''
        return cls(rowid, name, target, interaction.user, datetime.datetime.today(), privacy) # type: ignore

    @staticmethod
    def exists(interaction: discord.Interaction, title: str) -> bool:
        return queries.check_existance(interaction, title)
    
    async def is_owner(self, user: discord.User) -> bool:
        return queries.check_ownership(self.id, user)
        
    async def owner_level(self, user: discord.User) -> PermissionLevel:
        return PermissionLevel(queries.check_owner_level(self.id, user))
        
    async def set_owner(self, user: discord.Member | discord.User, permission_level: PermissionLevel) -> None:
        queries.set_ownership_lvl(**{'pid': self.id, 'oid': user.id, 'plvl': permission_level.value})

    async def set_privacy(self, permission_level: PermissionLevel) -> None:
        queries.set_privacy_level(self.id, permission_level.value)