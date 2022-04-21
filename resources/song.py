from typing import TYPE_CHECKING, Any
import discord
import datetime
import pytz

from .utils import (
    Connector,
    NotASong,

)

from .utils import spotify as sp
from .utils import youtube as yt


__all__ = (
    'Song',
    'ESong',
    'VSong'
)

class Song:

    if TYPE_CHECKING:
        title: str
        url: str
        artist: str
        author: str
        album: str
        thumbnail: str
        duration: str
        year: int

    
    def __init__(self, **kwargs):
        
        if 'available_markets' in kwargs:
            # Spotify infos
            kwargs = kwargs
            self.title = kwargs['name']
            self.artist = kwargs['artists'][0]['name']
            self.author = kwargs['artists'][0]['name']
            self.album = kwargs['album']['name']
            self.thumbnail = kwargs['album']['images'][0]['url']

            _cached_seconds = kwargs['duration_ms'] * 1000 # cached seconds are used to be stored into db
            minutes = _cached_seconds//60
            seconds = _cached_seconds - (minutes*60)
            self.duration = f"{minutes}:{seconds}"

            self.year = int(kwargs['album']['release_date'][:4])
            self.url = kwargs['external_urls']['spotify']

        else:
            # Youtube infos
            """
            if 'music' not in kwargs['tags']:
                raise NotASong('Use cortana for memes and sounds')"""

            self.title = kwargs['title']
            self.author = kwargs['uploader']
            self.artist = kwargs['uploader']

            self.album = kwargs.get('album', '\u200b')

            self.thumbnail = kwargs['thumbnail']

            self.duration = kwargs.get('duration_string', '-')
            
            self.year = int(kwargs['upload_date'][:4])
            self.url = kwargs['original_url']
            self.source = kwargs['url']

        self.id = kwargs['id']


    def upload(self, playlist_id: str):
        with Connector() as cur:
            cur.execute(f"INSERT INTO songs (playlist_id, id) VALUES ({playlist_id}, '{self.id}');")

    @classmethod
    def from_database(cls, id: str):
        if len(id) == 11:
            info = yt.from_link(f'https://www.youtube.com/watch?v={id}')
            return cls(**info)
        # elif len(id) == 22:
        else:
            info = sp.track(id)
            return cls(**info)

    @classmethod
    def from_reference(cls, reference: str):
        info = sp.search(reference)
        if len(info['tracks']['items']) == 0:
            results = yt.search(reference)
            if results is None:
                return None
            infos = results
            if len(infos) == 0:
                return None

        else:
            infos: list[dict[str, Any]] = [i for i in info['tracks']['items']]

        for info in infos:
            yield cls(**info)

    @classmethod
    def from_spotify(cls, link: str):
        if 'track' not in link:
            return None

        info = sp.track(link.split('/')[-1].split('?')[0])
        return cls(**info)

    @classmethod
    def from_youtube(cls, link: str):
        info = yt.from_link(link)
        return cls(**info)

    @classmethod
    async def from_data(cls, reference: str, interaction: discord.Interaction):
        songs: list[Song] = []
        if not reference.startswith('http'):
            for song in Song.from_reference(reference):
                if song is not None:
                    songs.append(song)

            if len(songs) == 0:
                await interaction.response.send_message(embed=discord.Embed(title='Could not find anything :c', description=f'Searching `{reference}` returned no result.', color=discord.Color.dark_red()))
                return

        elif 'open.spotify.com' in reference:
            song = Song.from_spotify(reference)
            if song is None:
                await interaction.response.send_message(embed=discord.Embed(title='Link returned no result.', description=f'(This link)[{reference}] returned no result.', color=discord.Color.dark_red()))
                return

            songs = [song]
        
        elif 'https://youtu.be' in reference or 'youtube.com' in reference:
            try:
                song = Song.from_youtube(reference)
            except NotASong:
                await interaction.response.send_message(embed=discord.Embed(title='Link returned no result.', description=f'(This link)[{reference}] returned no result.', color=discord.Color.dark_red()))
                return
            
            songs = [song]
        
        else:
            await interaction.response.send_message(embed=discord.Embed(title='Bad Request', description=f'`{reference}`-like links are not supported'))
            return

        if len(songs) > 1:
            embeds: list[ESong] = []
            for song in songs:
                embeds.append(ESong(song))

        
            view = VSong(embeds)
            await interaction.response.send_message(embed=embeds[0], view=view)
            await view.wait()

            songs = [view.current_song.song]

        return songs[0]



## TODO: Rewrite everything under here. No need to subclass embed
class ESong(discord.Embed):
    
    def __init__(self, song: Song, confirm: bool = True):
        now = datetime.datetime.now(tz=pytz.timezone('Europe/Rome'))
        super().__init__(
            color=discord.Color.dark_purple(),
            title=song.title,
            description=f'{song.artist} • {song.album}',
            url=song.url,
            timestamp=now
            )
        self.song = song
        self.confirm = confirm


class VSong(discord.ui.View):

    def __init__(self, songs: list[ESong]):
        super().__init__()
        self.songs = songs
        self.current_song: ESong = self.songs[0]

        self.index = 0

    @property
    def index(self) -> int:
        return self.__index

    @index.setter
    def index(self, value: int):
        assert (0 <= value <= len(self.songs) - 1), f'Value set for index: {value}'

        self.current_song = self.songs[value]

        children: list[discord.ui.Button] = self.children # type: ignore

        children[-1].disabled = not self.current_song.confirm
        children[0].disabled = children[1].disabled = not value
        children[2].disabled = children[3].disabled = value == len(self.songs) -1

        self.__index = value

    @discord.ui.button(label='<<')
    async def _to_first(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = 0

        await interaction.response.edit_message(embed=self.current_song, view=self)

    @discord.ui.button(label='<')
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index -= 1

        await interaction.response.edit_message(embed=self.current_song, view=self)

    @discord.ui.button(label='>')
    async def fowrard(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index += 1

        await interaction.response.edit_message(embed=self.current_song, view=self)

    @discord.ui.button(label='>>')
    async def _to_last(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = len(self.songs) - 1

        await interaction.response.edit_message(embed=self.current_song, view=self)

    @discord.ui.button(label='✓', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = len(self.songs) - 1

        await interaction.response.defer()
        await interaction.message.delete() # type: ignore
        self.stop()
