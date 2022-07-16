from dataclasses import dataclass

import discord
import json

from .utils import (
    BadRequest,
    NotFound,
    WrongLink
)

from connections import (
    Connector,
    SongCache,
)

from .utils import spotify as sp
from .utils import youtube as yt

from ui.songs import VSong


__all__ = (
    'Song',
    'search',
    'choose'
)


class SpotifyInfo(dict):
    def __init__(self, **kwargs) -> None:
        title = kwargs['name']
        author = kwargs['artists'][0]['name']

        yt_data = yt.search(f'{title} {author}')[0]
        youtube = yt_data['original_url']
        source = yt_data['url']

        _d = kwargs['duration']//1000
        mins = _d//60
        secs = _d - mins * 60
        if secs < 10:
            secs = f"0{secs}"
        duration = f"{mins}:{secs}"
                
        _dict = {
            'id': kwargs['id'],
            'title': title,
            'author': author,
            'album': kwargs['album']['name'],
            'thumbnail': kwargs['album']['images'][0]['url'],
            'duration': duration,
            'year': int(kwargs['album']['release_date'][:4]),
            'spotify': kwargs['external_urls']['spotify'],
            'youtube': youtube,
            'source': source
            }
        super().__init__(_dict)

class YTInfo(dict):
    def __init__(self, **kwargs) -> None:

        _dict = {
            'id': kwargs['id'],
            'title': kwargs['title'],
            'author': kwargs['uploader'],
            'album': kwargs.get('album', '\u200b'),
            'thumbnail': kwargs['thumbnail'],
            'duration': kwargs['duration_string'],
            'year': kwargs['upload_date'][:4],
            'youtube': kwargs['original_url'],
            'source': kwargs['url']
        }
        super().__init__(_dict)

class DataInfo(dict):
    def __init__(self, *args) -> None:
        source = ''
        if args[7]:
            with SongCache() as cache:
                source = cache[args[7]]
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
        songs = Song.from_reference(reference, playable)

        if len(songs) == 0:
            raise NotFound(f'Searching `{reference}` returned no result.')

    elif 'open.spotify.com' in reference:
        song = Song.from_spotify(reference)
        if song is None:
            raise WrongLink(f'(This link)[{reference}] returned no result.')
        
        if playable and not song.source:
            songs = Song.from_reference(f'{song.title} {song.author}', playable)
        else:
            songs = [song]
    
    elif 'youtu.be' in reference or 'youtube.com' in reference:
        song = Song.from_youtube(reference)
        songs = [song]
    
    else:
        raise BadRequest(f'(This type of links)[{reference}] are not supported.')
    
    if playable:
        for song in songs:
            song.upload()

    return songs

async def choose(interaction: discord.Interaction, reference: str, playable: bool = False):
    songs = search(reference, playable)
    
    if len(songs) > 1:
        view = VSong(songs, choice=True)
        if interaction.response.is_done():
            await interaction.followup.send(embed=songs[0].embed, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(embed=songs[0].embed, view=view, ephemeral=True)
        await view.wait()
        song = view.current_song
    else:
        song = songs[0]

    with SongCache() as cache:
        cache[reference] = song.id

    return song

@dataclass
class Song:

    id: int | str
    title: str
    author: str
    album: str
    thumbnail: str
    duration: str
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
        self.embed.set_thumbnail(url=self.thumbnail)
        self.embed.add_field(name='Year', value=self.year)
        self.embed.add_field(name='Duration', value=self.duration)
        
        if self.spotify:
            with Connector() as cur:
                cur.execute("SELECT * FROM Songs WHERE Spotify=?;", (self.spotify,))
                data = cur.fetchone()
            if data is not None:
                if self.id == data[0]:
                    return
                self.update_info()
                return
        self.upload()

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Song) and __o.id == self.id

    def __ne__(self, __o: object) -> bool:
        return not self.__eq__(__o)

    def upload(self) -> None:
        with Connector() as cur:
            cur.execute(f"""INSERT INTO Songs (ID, Title, Author, Album, Thumbnail, Duration, Year, Spotify, Youtube, Source) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
            (self.id, self.title, self.author, self.album, self.thumbnail, self.duration, self.year, self.spotify, self.youtube, self.source)
            )

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
            data = yt.search(f'{self.title} {self.author}')[0]
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
            SET ID=?,
                TItle=?,
                Author=?,
                Album=?,
                Thumbnail=?,
                Year=?
            WHERE Spotify=?;""",
            (self.id, self.title, self.author, self.album, self.thumbnail, self.year, self.spotify))

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
    def from_reference(cls, reference: str, playable: bool = False) -> list['Song']:
        with SongCache() as cache:
            if reference in cache:
                song_id = cache[reference]
                self = cls.from_id(song_id)
                if playable and self.source == '':
                    self.update_source()
                return [self]

        songs = []
        if not playable:
            info = sp.search(reference)
            if len(info['tracks']['items']) > 0:

                for track in info['tracks']['items']:
                    info = SpotifyInfo(**track)
                    songs.append(cls(**info))
        else:
            results = yt.search(reference)
            for result in results:
                info = YTInfo(**result)
                songs.append(cls(**info))
        
        return songs

    @classmethod
    def from_spotify(cls, link: str):
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
