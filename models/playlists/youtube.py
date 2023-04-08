from typing import Self

import discord
import yarl

from .permissions import PlaylistPermission
from .base import Base
from models.songs import YTMusicSong
from models.utils.youtube import playlist



class YouTubePlaylist(Base[YTMusicSong]):

    @classmethod
    def get(cls, interaction: discord.Interaction, url: str) -> Self:
        _url = yarl.URL(url)
        if _url.host == 'www.youtube.com' or _url.host == 'music.youtube.com':
            playlist_id = _url.query['v']
        elif _url.host == 'youtu.be':
            playlist_id = _url.name
        else:
            raise TypeError(f'YouTube url is neither www.youtube.com/music.youtube.com nor youtu.be, but: {url}')
        if not playlist_id.startswith('PL'):
            raise FileNotFoundError # TODO: create custom exception
        
        data = playlist(playlist_id)
        target = interaction.guild or interaction.user
        self = cls(data['id'], data['title'], target, interaction.user, data['year'], PlaylistPermission.Admin) # type: ignore

        for track in data['tracks']:
            self.append(YTMusicSong.create(track))
        return self