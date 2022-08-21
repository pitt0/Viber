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

from ui.songs import VSong


__all__ = (
    'Song',
    'search',
    'choose'
)

def duration_string(ms: int) -> str:
    duration = ms//1000
    mins = duration//60
    secs = duration - mins * 60
    if secs < 10:
        secs = f"0{secs}"
    return f"{mins}:{secs}"

class SpotifyInfo(dict):
    def __init__(self, **kwargs) -> None:
        title = kwargs['name']
        author = kwargs['artists'][0]['name']

        yt_data = yt.search(f'{title} {author}')[0]
        youtube = yt_data['original_url']
        source = yt_data['url']

        duration = duration_string(kwargs['duration_ms'])
                
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
        youtube = args[8] or yt.search_urls(args[1] + ' ' + args[2])[0]
        source = args[9] or ''
        if not source:
            data = yt.from_link(youtube)
            source = data['url']

            with Connector() as cur:
                cur.execute("""UPDATE Songs
                SET Source=?,
                    Youtube=?
                WHERE ID=?;""",
                (source, youtube, args[0]))

        _dict = {
            'id': args[0],
            'title': args[1],
            'author': args[2],
            'album': args[3],
            'thumbnail': args[4],
            'duration': args[5],
            'year': args[6],
            'spotify': args[7],
            'youtube': youtube,
            'source': source
        }
        super().__init__(_dict)

def fetch_songs(reference: str) -> list['Song']:
    print('helo')
    songs: list[Song] = []
    if not reference.startswith('http'):
        songs = Song.from_reference(reference)

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

def search(reference: str) -> 'Song':
    song = fetch_songs(reference)[0]
    song.lyrics = genius.lyrics(song)
    song.upload(reference)
    return song

async def choose(interaction: discord.Interaction, reference: str):
    songs = fetch_songs(reference)
    
    if len(songs) > 1:
        view = VSong(songs, choice=True)
        if interaction.response.is_done():
            await interaction.followup.send(embed=songs[0].embeds[0], view=view, ephemeral=True)
        else:
            await interaction.response.send_message(embed=songs[0].embeds[0], view=view, ephemeral=True)
        await view.wait()
        song = view.current_song
    else:
        song = songs[0]

    song.lyrics = genius.lyrics(song)
    song.upload(reference)
    return song



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
            max_len = 5 if len(tracks) > 5 else len(tracks)
            for track in tracks[: max_len]:
                info = SpotifyInfo(**track)
                songs.append(cls(**info))
        else:
            results = yt.search(reference)
            max_len = 5 if len(results) > 5 else len(results)
            for result in results[: max_len]:
                info = YTInfo(**result)
                songs.append(cls(**info))
        return songs

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

        
        now = datetime.datetime.now()
        print(f"[{now.strftime('%H:%M:%S')}] Checking spotify database...")
        track = sp.track(link.split('/')[-1].split('?')[0])
        
        now = datetime.datetime.now()
        print(f"[{now.strftime('%H:%M:%S')}] Formatting spotify info into dictionary...")
        info = SpotifyInfo(**track)
        
        now = datetime.datetime.now()
        print(f"[{now.strftime('%H:%M:%S')}] returning...")
        return cls(**info)

    @classmethod
    def from_youtube(cls, link: str):
        
        now = datetime.datetime.now()
        print(f"[{now.strftime('%H:%M:%S')}] Checking database for youtube link...")
        with Connector() as cur:
            cur.execute(f"SELECT * FROM Songs WHERE Youtube='{link}';")
            song = cur.fetchone()
            if song is not None:
                return cls.from_database(song)

        
        now = datetime.datetime.now()
        print(f"[{now.strftime('%H:%M:%S')}] Checking youtube database...")
        track = yt.from_link(link)
        
        now = datetime.datetime.now()
        print(f"[{now.strftime('%H:%M:%S')}] Formatting youtube info into dictionary...")
        info = YTInfo(**track)
        
        now = datetime.datetime.now()
        print(f"[{now.strftime('%H:%M:%S')}] returning...")
        return cls(**info)
