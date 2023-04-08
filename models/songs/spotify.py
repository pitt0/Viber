from functools import cached_property
from typing import Any, Literal, Self
from typing import overload

import discord
import yarl

from .base import *
from .local import LocalSong
from models.requests.local import SpotifyRequest, SpotifyAlbumRequest
from models.requests.web.spotify import track, search

from resources import Time
from resources.typings import spotify



class SpotifyArtist(Artist):

    id: str

    @classmethod
    def create(cls, data: spotify.ArtistEntry) -> Self:
        url = data['external_urls'].get('spotify', f"https://open.spotify.com/artist/{data['id']}")
        return cls(data['id'], data['name'], url)



class SpotifyAlbum(Album):

    id: str

    async def dump(self) -> None:
        await SpotifyAlbumRequest.dump(self.id, self.name, self.authors, self.thumbnail, self.release_date)

    @classmethod
    def load(cls, id: str) -> Self:
        artists = []
        data = SpotifyRequest.get(id)
        for _, name, _, _, artst_id in data:
            artists.append(Artist(artst_id, name, f'https://open.spotify.com/artist/{artst_id}'))
        name, _, rd, thumbnail, _ = data[0]
        return cls(id, name, artists, thumbnail, rd, f'https://open.spotify.com/album/{id}')

    @classmethod
    def create(cls, data: spotify.AlbumEntry) -> Self:
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
        await self.album.dump()
        rowid = await SpotifyRequest.dump(self.id, self.title, self.album.id, self.artists, self.duration)
        return LocalSong.load(rowid)

    @classmethod
    def load(cls, id: str) -> Self:
        artists = []
        data = SpotifyRequest.get(id)
        for _, _, name, _, artst_id in data:
            artists.append(Artist(artst_id, name, f'https://open.spotify.com/artist/{artst_id}'))
        title, album_id, _, duration, _ = data[0]
        album = SpotifyAlbum.load(album_id)
        return cls(id, title, artists, album, duration, f'https://open.spotify.com/track/{id}')


    @classmethod
    def create(cls, data: spotify.TrackData) -> Self:
        artists = [SpotifyArtist.create(artist) for artist in data['artists']]
        album = SpotifyAlbum.create(data['album']) # type: ignore
        return cls(data['id'], data['name'], artists, album, Time.from_ms(data['duration_ms']), f"https://open.spotify.com/track/{data['id']}")

    @classmethod
    def get(cls, url: str) -> spotify.TrackData:
        _url = yarl.URL(url)
        return track(str(_url.name))

    @overload
    @classmethod
    def search(cls, query: str, limit: Literal[1] = 1) -> spotify.TrackData:
        ...

    @overload
    @classmethod
    def search(cls, query: str, limit: int = 1) -> list[spotify.TrackData]:
        ...

    @classmethod
    def search(cls, query: str, limit: int = 1) -> Any:
        songs = search(query)
        if limit == 1:
            return songs[0]
        return songs