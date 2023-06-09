from typing import Self

import dateutil.parser as dparser
import discord
import yarl

from .permissions import PermissionLevel
from .base import Base
from .local import LocalPlaylist
from api.local.playlist import dump
from api.web.spotify import playlist
from models.songs import SpotifySong



class SpotifyPlaylist(Base[SpotifySong]):

    id: str

    @classmethod
    def get(cls, interaction: discord.Interaction, url: str) -> Self:
        _url = yarl.URL(url)
        data = playlist(_url.name)
        target = interaction.guild or interaction.user
        date = data['tracks']['items']['added_at']
        self = cls(data['id'], data['name'], target, interaction.user, dparser.parse(date, yearfirst=True), PermissionLevel.Admin) # type: ignore

        for track in data['tracks']['items']:
            self.append(SpotifySong.create(track['track']))
        return self
    
    async def dump(self, interaction: discord.Interaction) -> LocalPlaylist:
        target = interaction.guild or interaction.user
        local_id = dump(self.id, 'spotify', self.title, target.id, interaction.user.id)
        return await LocalPlaylist.load(interaction, local_id)