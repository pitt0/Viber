from dataclasses import dataclass
from typing import Generator

import discord
import json

from .utils import (
    BadRequest,
    Connector,
    NotFound,
    WrongLink
)

from .utils import spotify as sp
from .utils import youtube as yt


__all__ = (
    'Song',
    'search'
)


class SpotifyInfo(dict):
    def __init__(self, **kwargs) -> None:
        urls = yt.search_urls(kwargs['name'] + ' ' + kwargs['artists'][0]['name'])
        youtube = ''
        source = ''
        if urls:
            youtube = urls[0]
            with open('database/song_cache.json') as f:
                source = json.load(f)[youtube]
        _dict = {
            'id': kwargs['id'],
            'title': kwargs['name'],
            'author': kwargs['artists'][0]['name'],
            'album': kwargs['album']['name'],
            'thumbnail': kwargs['album']['images'][0]['url'],
            'duration': kwargs['duration_ms']*1000,
            'year': int(kwargs['album']['release_date'][:4]),
            'spotify': kwargs['external_urls']['spotify'],
            'youtube': youtube,
            'source': source
            }
        super().__init__(_dict)

class YTInfo(dict):
    def __init__(self, **kwargs) -> None:
        minutes, seconds = kwargs['duration_string'].split(':')
        duration = int(seconds) + int(minutes)*60
        _dict = {
            'id': kwargs['id'],
            'title': kwargs['title'],
            'author': kwargs['uploader'],
            'album': kwargs.get('album', '\u200b'),
            'thumbnail': kwargs['thumbnail'],
            'duration': duration,
            'year': kwargs['upload_date'][:4],
            'youtube': kwargs['original_url'],
            'source': kwargs['url']
        }
        super().__init__(_dict)

class DataInfo(dict):
    def __init__(self, *args) -> None:
        source = ''
        if args[7]:
            with open('database/song_cache.json') as f:
                source = json.load(f)[args[7]]
        _dict = {
            'id': args[0],
            'title': args[1],
            'author': args[2],
            'album': args[3],
            'thumbnail': args[4],
            'duration': args[5],
            'year': args[6],
            'youtube': args[7],
            'source': source
        }
        super().__init__(_dict)


def search(reference: str, playable: bool = False) -> list['Song']:
    songs: list[Song] = []
    if not reference.startswith('http'):
        for song in Song.from_reference(reference, playable):
            songs.append(song)

        if len(songs) == 0:
            raise NotFound(f'Searching `{reference}` returned no result.')

    elif 'open.spotify.com' in reference:
        song = Song.from_spotify(reference)
        if song is None:
            raise WrongLink(f'(This link)[{reference}] returned no result.')

        songs = [song]
    
    elif 'youtu.be' in reference or 'youtube.com' in reference:
        song = Song.from_youtube(reference)
        songs = [song]
    
    else:
        raise BadRequest(f'(This type of links)[{reference}] are not supported.')

    return songs

@dataclass
class Song:

    id: int | str
    title: str
    author: str
    album: str
    thumbnail: str
    duration: int
    year: int

    spotify: str = ''
    youtube: str = ''

    source: str = ''

    def __post_init__(self) -> None:
        self.url = self.spotify or self.youtube
        self.embed = discord.Embed(
            color=discord.Color.dark_purple(),
            title=self.title,
            description=f'{self.author} • {self.album}',
            url=self.url
        )
        if self.url and self.source:
            source = {self.url: self.source}
            with open('database/song_cache.json', 'w') as f:
                json.dump(source, f, indent=4)


    def upload(self, playlist_id: int) -> None:
        with Connector() as cur:
            cur.execute(f"""INSERT INTO Songs (ID, Title, Author, Album, Thumbnail, Duration, Year, Spotify, Youtube, PlaylistID) 
            VALUES ({self.id}, ?, ?, ?, '{self.thumbnail}', {self.duration}, {self.year}, '{self.spotify}', '{self.youtube}', ?);""", (self.title, self.author, self.album, playlist_id))

    def remove(self, playlist_id: int) -> None:
        with Connector() as cur:
            cur.execute(f"DELETE FROM Songs WHERE PlaylistID=? AND SongID=?;", (playlist_id, self.id,))

    @classmethod
    def from_database(cls, data: tuple[str | int, ...]):
        info = DataInfo(*data)
        return cls(**info)

    @classmethod
    def from_reference(cls, reference: str, playable: bool = False) -> Generator['Song', None, None]:
        info = sp.search(reference)
        if len(info['tracks']['items']) > 0 and not playable:
            for track in info['tracks']['items']:
                info = SpotifyInfo(**track)
                yield cls(**info)
        else:
            results = yt.search(reference)
            for result in results:
                info = YTInfo(**result)
                yield cls(**info)

    @classmethod
    def from_spotify(cls, link: str):
        if 'track' not in link:
            return None

        track = sp.track(link.split('/')[-1].split('?')[0])
        info = SpotifyInfo(**track)
        return cls(**info)

    @classmethod
    def from_youtube(cls, link: str):
        track = yt.from_link(link)
        info = YTInfo(**track)
        return cls(**info)
