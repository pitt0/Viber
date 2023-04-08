from typing import Self

import dateutil.parser as dparser
import discord
import yarl

from .permissions import PlaylistPermission
from .base import Base
from models.songs import SpotifySong
from models.requests.web.spotify import playlist



class YouTubePlaylist(Base[SpotifySong]):

    @classmethod
    def get(cls, interaction: discord.Interaction, url: str) -> Self:
        _url = yarl.URL(url)
        data = playlist(_url.name)
        target = interaction.guild or interaction.user
        date = data['tracks']['items']['added_at']
        self = cls(data['id'], data['name'], target, interaction.user, dparser.parse(date, yearfirst=True), PlaylistPermission.Admin) # type: ignore

        for track in data['tracks']['items']:
            self.append(SpotifySong.create(track['track']))
        return self