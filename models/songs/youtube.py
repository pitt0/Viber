import discord
import yarl

from .base import *
from .local import LocalSong
from api.local.albums import dump as album_dump
from api.local.songs import dump as song_dump
from api.web.youtube import item, album, search, source
from functools import cached_property
from resources import SongCache
from typing import Any, Literal, Self
from typing import overload



class YTMusicArtist(Artist):

    id: str

    def __init__(self, id: str, name: str) -> None:
        super().__init__(id, name, f'https://music.youtube.com/channel/{id}')

    @classmethod
    def create(cls, data: dict[str, Any]) -> Self:
        return cls(data['id'], data['name'])



class YTMusicAlbum(Album):

    id: str

    async def dump(self) -> int:
        return await album_dump(self.id, 'youtube', self.authors, name=self.name, thumbnail=self.thumbnail, release_date=self.release_date)

    @classmethod
    def create(cls, data: dict[str, Any]) -> Self:
        complete = album(data['id'])
        artists = [YTMusicArtist.create(art) for art in complete['artists']]
        return cls(data['id'], complete['title'], artists, complete['thumbnails'][0]['url'], complete['year'], f"https://music.youtube.com/playlist?list={complete['audioPlaylistId']}")



class YTMusicSong(Track):

    id: str
    reference: str

    @cached_property
    def source(self) -> str:
        print(f'Fetching source url of {self}') # NOTE: Log
        return source(self.url)

    @cached_property
    def thumbnail(self) -> str:
        return self.album.thumbnail

    @cached_property
    def embed(self) -> discord.Embed:
        return super().embed.set_thumbnail(url=self.thumbnail)
    
    async def dump(self) -> LocalSong:
        album_id = await self.album.dump()
        rowid = await song_dump(self.id, 'youtube', self.artists, title=self.title, album_id=album_id, duration=self.duration)
        if self.__getattribute__('reference'):
            SongCache.add(self.reference, rowid)
        return LocalSong.load(rowid)

    @classmethod
    def create(cls, data: dict[str, Any]) -> Self:
        artists = [YTMusicArtist.create(art) for art in data['artists']]
        album = YTMusicAlbum.create(data['album'])
        return cls(data['videoId'], data['title'], artists, album, data['duration'], f"https://music.youtube.com/watch?v={data['videoId']}")

    @classmethod
    def get(cls, url: str) -> dict[str, Any]:
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
    def search(cls, query: str, limit: Literal[1] = 1) -> dict[str, Any]:
        ...

    @overload
    @classmethod
    def search(cls, query: str, limit: int = 1) -> list[dict[str, Any]]:
        ...

    @classmethod
    def search(cls, query: str, limit: int = 1) -> Any:
        cls.reference = query
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