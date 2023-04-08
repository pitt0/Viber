from functools import cached_property
from typing import Any, Literal, Self
from typing import overload

import discord
import yarl

from .base import *
from models.utils.youtube import item, album, search, source
from resources.requests import YouTubeRequest, YouTubeAlbumRequest
from resources.typings import ytmusic



class YTMusicArtist(Artist):

    def __init__(self, id: str, name: str) -> None:
        super().__init__(id, name, f'https://music.youtube.com/channel/{id}')

    @classmethod
    def create(cls, data: ytmusic.Artist) -> Self:
        return cls(data['id'], data['name'])



class YTMusicAlbum(Album):

    async def dump(self) -> None:
        await YouTubeAlbumRequest.dump(self.id, self.name, self.authors, self.thumbnail, self.release_date)

    @classmethod
    def load(cls, id: str) -> Self:
        artists = []
        data = YouTubeAlbumRequest.get(id)
        for _, name, _, _, artst_id in data:
            artists.append(YTMusicArtist(artst_id, name))
        name, _, rd, thumbnail, _ = data[0]
        return cls(id, name, artists, thumbnail, rd, f'https://music.youtube.com/playlist?list={id}')

    @classmethod
    def create(cls, data: ytmusic.Album) -> Self:
        partial = search(data['name'], 'albums', limit=1)[0]
        complete = album(partial['browseId'])
        artists = [YTMusicArtist.create(art) for art in complete['artists']]
        return cls(partial['browseId'], complete['title'], artists, complete['thumbnails'][0]['url'], complete['year'], f"https://music.youtube.com/playlist?list={complete['audioPlaylistId']}")



class YTMusicSong(Track):

    @cached_property
    def source(self) -> str:
        print(f'Fetching source url of {self}') # NOTE: Log
        return source(self.url)

    @cached_property
    def thumbnail(self) -> str:
        return self.album.thumbnail

    @cached_property
    def embed(self) -> discord.Embed:
        return discord.Embed(
            title=self.title,
            description=self._embed_artists,
            color=discord.Colour.dark_purple()
        ).set_thumbnail(url=self.thumbnail)
    
    async def dump(self) -> None:
        await self.album.dump()
        await YouTubeRequest.dump(self.id, self.title, self.album.id, self.artists, self.duration)
    
    @classmethod
    def load(cls, id: str) -> Self:
        artists = []
        data = YouTubeRequest.get(id)
        for _, _, name, _, artst_id in data:
            artists.append(YTMusicArtist(artst_id, name))
        title, album_id, _, duration, _ = data[0]
        album = YTMusicAlbum.load(album_id)
        return cls(id, title, artists, album, duration, f'https://music.youtube.com/watch?v={id}')

    @classmethod
    def create(cls, data: ytmusic.SongResult) -> Self:
        artists = [YTMusicArtist.create(art) for art in data['artists']]
        album = YTMusicAlbum.create(data['album'])
        return cls(data['videoId'], data['title'], artists, album, data['duration'], f"https://music.youtube.com/watch?v={data['videoId']}")
    
    @classmethod
    def get(cls, url: str) -> ytmusic.SongData:
        _url = yarl.URL(url)
        if _url.host == 'www.youtube.com' or _url.host == 'music.youtube.com':
            video_id = _url.query['v']
        elif _url.host == 'youtu.be':
            video_id = _url.name
        else:
            raise TypeError(f'YouTube url is neither www.youtube.com/music.youtube.com nor youtu.be, but: {url}')
        return item(video_id)

    @overload
    @classmethod
    def search(cls, query: str, limit: Literal[1] = 1) -> ytmusic.SongResult:
        ...

    @overload
    @classmethod
    def search(cls, query: str, limit: int = 1) -> list[ytmusic.SongResult]:
        ...

    @classmethod
    def search(cls, query: str, limit: int = 1) -> Any:
        data = search(query, 'songs', limit)
        if limit == 1:
            return data[0]
        return data



# class YouTubeVideo(Track):

#     def __init__(self, id: str, title: str, uploader: Artist, source: str, thumbnail: str):
#         super().__init__(id, title, [uploader])
#         self._source = source
#         self.thumbnail = thumbnail

#     @cached_property
#     def source(self) -> str:
#         return self._source
    
#     @cached_property
#     def embed(self) -> discord.Embed:
#         return discord.Embed(
#             title=self.title,
#             description=self.embed_artists,
#             color=discord.Colour.dark_purple()
#         ).set_thumbnail(url=self.thumbnail)

#     @classmethod
#     def create(cls, data: youtube.Result) -> Self:
#         uploader = Artist(data['uploader_id'], data['uploader'], data['uploader_url'])
#         thumbnail = "http://127.0.0.1"
#         for t in data['thumbnails']:
#             if t.get('resolution') == "480x360":
#                 thumbnail = t['url']
#         return cls(data['id'], data['title'], uploader, data['url'], thumbnail)

#     @overload
#     @classmethod
#     def search(cls, query: str, limit: Literal[1] = 1) -> youtube.Result:
#         ...

#     @overload
#     @classmethod
#     def search(cls, query: str, limit: int = 1) -> list[youtube.Result]:
#         ...

#     @classmethod
#     def search(cls, query: str, limit: int = 1) -> Any:
#         data = search(query, limit)
#         if limit == 1:
#             return data[0]
#         return data