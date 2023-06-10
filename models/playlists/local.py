from typing import Self

import datetime
import dateutil.parser as dparser
import discord
import api.queries as queries

from .permissions import PermissionLevel
from .base import Base
from api.local import playlist
from models.songs import LocalSong
from resources.types import MISSING


__all__ = ('LocalPlaylist',)


class LocalPlaylist(Base[LocalSong]):

    @classmethod
    async def load(cls, interaction: discord.Interaction, id: int = MISSING, title: str = MISSING, target_id: int = MISSING) -> Self:
        data = playlist.get(id, title, target_id)
        try:
            target = await interaction.client.fetch_guild(data[2])
        except discord.NotFound:
            target = await interaction.client.fetch_user(data[2])
        user = await interaction.client.fetch_user(data[3])
        self = cls(data[0], data[1], target, user, dparser.parse(data[4], yearfirst=True), PermissionLevel(data[5]))

        songs = queries.read('select song_id from playlist_songs where playlist_id = ?;', (id,))
        for song in songs:
            song = LocalSong.load(song[0])
            self.append(song)

        self.__client = interaction.client
        return self

    @classmethod
    def create(cls, name: str, interaction: discord.Interaction, privacy: PermissionLevel) -> Self:
        target = interaction.guild or interaction.user
        rowid = playlist.dump('', 'local', name, target.id, interaction.user.id, privacy.value) # HACK: provider_id set as ''
        return cls(rowid, name, target, interaction.user, datetime.datetime.today(), privacy) # type: ignore

    @staticmethod
    def exists(interaction: discord.Interaction, title: str) -> bool:
        target = interaction.guild or interaction.user
        query = 'select 1 from playlists where target_id = ? and author_id = ? and playlist_title = ?;'
        return queries.check(query, (target.id, interaction.user.id, title))
    
    async def is_owner(self, user: discord.User) -> bool:
        return queries.check('select 1 from playlist_owners where playlist_id = ? and owner_id = ?;', (self.id, user.id))
        
    async def owner_level(self, user: discord.User) -> PermissionLevel:
        query = 'select permission_lvl from playlist_owners where playlist_id = ? and owner_id = ?;'
        level = queries.read(query, (id, user.id))[0][0]
        return PermissionLevel(level)
        
    async def set_owner(self, user: discord.Member | discord.User, permission_level: PermissionLevel) -> None:
        query = (
            'insert into playlist_owners (playlist_id, owner_id, permission_lvl) values (:pid, :oid, :plvl) '
            'on conflict do update set permission_lvl = :plvl;'
        )
        queries.write(query, {'pid': self.id, 'oid': user.id, 'plvl': permission_level.value})

    async def set_privacy(self, permission_level: PermissionLevel) -> None:
        queries.write('update playlists set privacy = ? where rowid = ?;', (self.id, permission_level.value))