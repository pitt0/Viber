from functools import cached_property
from typing import Any, Literal, Self
from typing import overload

import discord
import yarl

from .base import *
from .local import LocalSong
from api.local.albums import dump as album_dump
from api.local.songs import dump as song_dump
from api.web.spotify import track, search
from resources import Time



class SpotifyArtist(Artist):

    id: str

    @classmethod
    def create(cls, data: dict[str, Any]) -> Self:
        url = data['external_urls'].get('spotify', f"https://open.spotify.com/artist/{data['id']}")
        return cls(data['id'], data['name'], url)



class SpotifyAlbum(Album):

    id: str

    async def dump(self) -> int:
        return await album_dump(self.id, 'spotify', self.authors, name=self.name, thumbnail=self.thumbnail, release_date=self.release_date)

    @classmethod
    def create(cls, data: dict[str, Any]) -> Self:
        artists = [SpotifyArtist.create(artist) for artist in data['artists']]
        return cls(data['id'], data['name'], artists, data['images'][0]['url'], data['release_date'], f"https://open.spotify.com/album/{data['id']}")



class SpotifySong(Track):

    id: str

    @cached_property
    def thumbnail(self) -> str:
        return self.album.thumbnail

    @cached_property
    def embed(self) -> discord.Embed:
        return super().embed.set_thumbnail(url=self.thumbnail)
    
    async def dump(self) -> LocalSong:
        album_id = await self.album.dump()
        rowid = await song_dump(self.id, 'spotify', self.artists, title=self.title, album_id=album_id, duration=self.duration)
        return LocalSong.load(rowid)

    @classmethod
    def create(cls, data: dict[str, Any]) -> Self:
        artists = [SpotifyArtist.create(artist) for artist in data['artists']]
        album = SpotifyAlbum.create(data['album']) # type: ignore
        return cls(data['id'], data['name'], artists, album, Time.from_ms(data['duration_ms']), f"https://open.spotify.com/track/{data['id']}")

    @classmethod
    def get(cls, url: str) -> dict[str, Any]:
        _url = yarl.URL(url)
        return track(str(_url.name))

    @overload
    @classmethod
    def search(cls, query: str, limit: Literal[1] = 1) -> dict[str, Any]:
        ...

    @overload
    @classmethod
    def search(cls, query: str, limit: int = 1) -> list[dict[str, Any]]:
        ...

    @classmethod
    def search(cls, query: str, limit: int = 1) -> Any:
        songs = search(query)
        if limit == 1:
            return songs[0]
        return songs