from dataclasses import dataclass

import datetime
import discord

from .utils import (
    BadRequest,
    NotFound,
    WrongLink
)

from connections import (
    Connector,
    SongCache,
)

from .utils import genius

from .utils import spotify as sp
from .utils import youtube as yt

from .utils.info import *

from ui.songs import VSong


__all__ = (
    'Song',
    'search',
    'choose'
)


def search_reference(reference: str) -> list['Song']:
    songs = Song.from_reference(reference)
    if len(songs) == 0:
        raise NotFound(f'Searching `{reference}` returned no result.')

    return songs

def search_spotify(link: str) -> 'Song':
    song = Song.from_spotify(link)
    if song is None:
        raise WrongLink(f'(This link)[{link}] returned no result.')
    
    return song


def fetch_songs(reference: str) -> list['Song']:
    if not reference.startswith('http'):
        return search_reference(reference)

    elif 'open.spotify.com' in reference:
        return [search_spotify(reference)]
    
    elif 'youtu.be' in reference or 'youtube.com' in reference:
        return [Song.from_youtube(reference)]
    
    raise BadRequest(f'(This type of links)[{reference}] are not supported.')

def fetch_song(reference: str) -> 'Song':
    if not reference.startswith('http'):
        return Song.first_reference(reference)

    elif 'open.spotify.com' in reference:
        return search_spotify(reference)
    
    elif 'youtu.be' in reference or 'youtube.com' in reference:
        return Song.from_youtube(reference)
    
    raise BadRequest(f'(This type of links)[{reference}] are not supported.')
    

def search(reference: str) -> 'Song':
    song = fetch_song(reference)
    song.lyrics = genius.lyrics(song)
    song.upload(reference)
    return song

async def choose(interaction: discord.Interaction, reference: str):
    songs = search_reference(reference)
    song = songs[0]
    
    if len(songs) > 1:
        view = VSong(songs, choice=True)
        if interaction.response.is_done():
            await interaction.followup.send(embed=songs[0].embeds[0], view=view, ephemeral=True)
        else:
            await interaction.response.send_message(embed=songs[0].embeds[0], view=view, ephemeral=True)
        await view.wait()
        song = view.current_song

    song.lyrics = genius.lyrics(song)
    song.upload(reference)
    return song


# TODO: Create different classes of Song that are used for different things, ex: EmbeddableSong, PlayableSong

# # TODO: Create a class to make choose function faster
# @dataclass
# class MetaSong:

#     title: str
#     author: str
#     album: str
#     thumbnail: str
#     duration: str
#     year: str
#     url: str

#     def __post_init__(self) -> None:
#         embed = discord.Embed(
#             color=discord.Color.dark_purple(),
#             title=self.title,
#             description=f'{self.author} • {self.album}',
#             url=self.url
#         )
#         embed.set_thumbnail(url=self.thumbnail)
#         embed.add_field(name='Year', value=self.year)
#         embed.add_field(name='Duration', value=self.duration)

#         self.embeds = [embed, None]


@dataclass
class Song:

    id: str
    title: str
    author: str
    album: str
    thumbnail: str
    duration: str
    year: int

    spotify: str = ''
    youtube: str = ''

    source: str = ''
    lyrics: str = ''

    def __post_init__(self) -> None:
        self.url = self.spotify or self.youtube
        embed = discord.Embed(
            color=discord.Color.dark_purple(),
            title=self.title,
            description=f'{self.author} • {self.album}',
            url=self.url
        )
        embed.set_thumbnail(url=self.thumbnail)
        embed.add_field(name='Year', value=self.year)
        embed.add_field(name='Duration', value=self.duration)

        self.embeds = [embed, None]
        
        if self.spotify != '':
            with Connector() as cur:
                cur.execute("SELECT * FROM Songs WHERE Youtube=?;", (self.youtube,))
                data = cur.fetchone()
            if data is not None:
                if self.title == data[1]:
                    return
                self.update_info()
                return

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Song) and __o.id == self.id

    def __ne__(self, __o: object) -> bool:
        return not self.__eq__(__o)

    def upload(self, reference: str | None = None) -> None:
        if reference and 'http' not in reference:
            self.cache(reference)
        try:
            with Connector() as cur:
                cur.execute(f"""INSERT INTO Songs (ID, Title, Author, Album, Thumbnail, Duration, Year, Spotify, Youtube, Source) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                (self.id, self.title, self.author, self.album, self.thumbnail, self.duration, self.year, self.spotify, self.youtube, self.source)
                )
        except Exception as e:
            print(e)

    def update_source(self) -> None:
        if self.youtube != '':
            data = yt.from_link(self.youtube)
            self.source = data['url']
            with Connector() as cur:
                cur.execute("""UPDATE Songs
                SET Source=?
                WHERE ID=?;""",
                (self.source, self.id))
        else:
            data = yt.search_info(f'{self.title} {self.author}')
            self.youtube = data['original_url']
            self.source = data['url']
            with Connector() as cur:
                cur.execute("""UPDATE Songs
                SET Source=?,
                    Youtube=?
                WHERE ID=?;""",
                (self.source, self.youtube, self.id))

    def update_info(self) -> None:
        with Connector() as cur:
            cur.execute("""UPDATE Songs
            SET Title=?,
                Author=?,
                Album=?,
                Thumbnail=?,
                Year=?
            WHERE Spotify=?;""",
            (self.id, self.title, self.author, self.album, self.thumbnail, self.year, self.spotify))

    def add_lyrics(self) -> None:
        self.lyrics = genius.lyrics(self)
        lyrics_embed = discord.Embed(
            title=self.title,
            description=self.lyrics,
            color=discord.Color.dark_purple(),
            url=self.url
        ).set_thumbnail(url=self.thumbnail)

        self.embeds[1] = lyrics_embed

    def cache(self, reference: str) -> None:
        with SongCache() as cache:
            cache[reference] = self.id

    @staticmethod
    def cached(reference: str) -> bool:
        with SongCache() as cache:
            return reference in cache

    @classmethod
    def from_cache(cls, reference: str) -> 'Song':
        with SongCache() as cache:
            song_id = cache[reference]
        with Connector() as cur:
            cur.execute("SELECT * FROM Songs WHERE ID=?;", (song_id,))
            data = cur.fetchone()
        self = cls.from_database(data)
        if self.source == '':
            self.update_source()
        return self

    @classmethod
    def from_id(cls, id: str | int):
        with Connector() as cur:
            cur.execute(f"SELECT * FROM Songs WHERE ID=?;", (id,))
            song = cur.fetchone()
        return cls.from_database(song)

    @classmethod
    def from_database(cls, data: tuple[str | int, ...]):
        info = DataInfo(*data)
        return cls(**info)

    @classmethod
    def from_reference(cls, reference: str) -> list['Song']:
        if cls.cached(reference):
            return [cls.from_cache(reference)]

        songs = []
        info = sp.search(reference)
        if len(info['tracks']['items']) > 0:
            tracks = info['tracks']['items']
            for track in tracks:
                info = SpotifyInfo(**track)
                songs.append(cls(**info))
        else:
            results = yt.search_infos(reference)
            for result in results:
                info = YTInfo(**result)
                songs.append(cls(**info))
        return songs

    @classmethod
    def first_reference(cls, reference: str) -> 'Song':
        if cls.cached(reference):
            return cls.from_cache(reference)

        info = sp.search(reference, limit=1)
        if len(info['tracks']['items']) > 0:
            track = info['tracks']['items'][0]
            info = SpotifyInfo(**track)
            return cls(**info)
        else:
            result = yt.search_info(reference)
            info = YTInfo(**result)
            return cls(**info)

    @classmethod
    def from_spotify(cls, link: str):
        now = datetime.datetime.now()
        print(f"[{now.strftime('%H:%M:%S')}] Checking database for spotify link...")
        with Connector() as cur:
            cur.execute(f"SELECT * FROM Songs WHERE Spotify='{link}';")
            song = cur.fetchone()
            if song is not None:
                return cls.from_database(song)

        if 'track' not in link:
            return None

        track = sp.track(link.split('/')[-1].split('?')[0])
        info = SpotifyInfo(**track)
        return cls(**info)

    @classmethod
    def from_youtube(cls, link: str):
        with Connector() as cur:
            cur.execute(f"SELECT * FROM Songs WHERE Youtube='{link}';")
            song = cur.fetchone()
            if song is not None:
                return cls.from_database(song)

        track = yt.from_link(link)
        info = YTInfo(**track)
        return cls(**info)
