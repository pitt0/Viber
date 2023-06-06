from typing import Self

import datetime
import dateutil.parser as dparser
import discord

from .permissions import PermissionLevel
from .base import Base
from models.requests import PlaylistRequest
from models.songs import LocalSong
from resources.connections import Connection
from resources.types import MISSING


__all__ = ('LocalPlaylist',)


class LocalPlaylist(Base[LocalSong]):

    @classmethod
    async def load(cls, interaction: discord.Interaction, id: int = MISSING, title: str = MISSING, target_id: int = MISSING) -> Self:
        data = PlaylistRequest.get(id, title, target_id)
        try:
            target = await interaction.client.fetch_guild(data[2])
        except discord.NotFound:
            target = await interaction.client.fetch_user(data[2])
        user = await interaction.client.fetch_user(data[3])
        self = cls(data[0], data[1], target, user, dparser.parse(data[4], yearfirst=True), PermissionLevel(data[5]))

        songs = PlaylistRequest.songs(self.id)
        for song in songs:
            # NOTE: if this is too slow, make SongPreview class that only uses title, author etc.
            song = LocalSong.load(song[0])
            self.append(song)

        self.__client = interaction.client
        return self

    @classmethod
    def create(cls, name: str, interaction: discord.Interaction, privacy: PermissionLevel) -> Self:
        target = interaction.guild or interaction.user
        rowid = PlaylistRequest.dump(name, target.id, interaction.user.id, privacy.value)
        return cls(rowid, name, target, interaction.user, datetime.datetime.today(), privacy) # type: ignore

    @staticmethod
    def exists(interaction: discord.Interaction, title: str) -> bool:
        target = interaction.guild or interaction.user
        with Connection() as cursor:
            cursor.execute('select 1 from playlists where target_id = ? and author_id = ? and playlist_title = ?;', (target.id, interaction.user.id, title))
            return bool(cursor.fetchone())
    
    async def is_owner(self, user: discord.User) -> bool:
        with Connection() as cursor:
            cursor.execute('select 1 from playlist_owners where playlist_id = ? and owner_id = ?;', (self.id, user.id))
            return bool(cursor.fetchone())
        
    async def owner_level(self, user: discord.User) -> PermissionLevel:
        with Connection() as cursor:
            cursor.execute('select permission_lvl from playlist_owners where playlist_id = ? and owner_id = ?;', (self.id, user.id))
            return PermissionLevel((cursor.fetchone() or [0])[0])
        
    async def set_owner(self, user: discord.Member | discord.User, permission_level: PermissionLevel) -> None:
        with Connection() as cursor:
            query = (
                'insert into playlist_owners (playlist_id, owner_id, permission_lvl) '
                'values (:pid, :oid, :plvl) '
                'on conflict do update '
                'set permission_lvl = :plvl;'
            )
            cursor.execute(query, {'pid': self.id, 'oid': user.id, 'plvl': permission_level.value})

    async def set_privacy(self, permission_level: PermissionLevel) -> None:
        with Connection() as cursor:
            query = (
                'update playlists '
                'set privacy = ? '
                'where rowid = ?;'
            )
            cursor.execute(query, (permission_level.value, self.id))