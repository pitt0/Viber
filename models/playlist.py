from abc import abstractclassmethod
from dataclasses import dataclass
from string import printable
from typing import Any, Optional, TYPE_CHECKING

import datetime
import discord

from connections import *
from .utils import *




__all__ = (
    'Advices',
    'LikedSongs',
    'Playlist',

    'CachedPlaylist',
)


@dataclass
class CachedPlaylist:
    name: str
    guild: int
    author: int

    @classmethod
    def load(cls) -> list['CachedPlaylist']:
        cache = []
        with Connector() as cur:
            cur.execute("SELECT * FROM Playlists;")
            for playlist in cur.fetchall():
                cache.append(CachedPlaylist(
                    playlist[1],
                    playlist[5],
                    playlist[4]
                    ))
        return cache
    
    def showable(self, interaction: discord.Interaction) -> bool:
        return interaction.guild.id == self.guild and interaction.user.id == self.author # type: ignore
    
    def is_input(self, query: str) -> bool:
        return query.lower() in self.name.lower()

@dataclass
class EmbeddablePlaylist:
    title: str
    date: str

class BasePlaylist:
    
    __slots__ = (
        'name',
        'songs',
        'id'
    )

    id: int
    
    def __init__(self, name: str):
        self.name = name

        self.songs = []

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, self.__class__) and __o.id == self.id

    def __ne__(self, __o: object) -> bool:
        return not self.__eq__(__o)

    def __repr__(self) -> str:
        return f'{self.name}#{self.id}'

    def __iter__(self):
        return (song for song in self.songs)

    def __contains__(self, song) -> bool:
        return song in self.songs

    def __create_embed(self, page: int) -> discord.Embed:
        if hasattr(self, 'user'):
            target = self.user # type: ignore
        else:
            target = self.author # type: ignore
        _e = discord.Embed(
            title=self.name,
            description=f"by {target.display_name}",
            color=discord.Color.blurple()
        )
        _e.set_footer(text=f'Page {page}')
        return _e


    @property
    def empty(self) -> bool:
        return len(self.songs) == 0

    @property
    def embeds(self) -> list[discord.Embed]:
        es = []
        current = 0

        _e = self.__create_embed(1)
        es.append(_e)
        for index, song in enumerate(self.songs):
            if index // 12 > current:
                current = index // 12
                _e = self.__create_embed(index//12)
                es.append(_e)
            _e.add_field(name=song.title, value=f"{song.author} • {song.album}", inline=True)
        return es

    def add_song(self, song) -> None:
        self.songs.append(song)

    def remove_song(self, song) -> None:
        self.songs.remove(song)
        
    @abstractclassmethod
    def from_database(cls, _) -> Optional['BasePlaylist']:
        """Retrives the Playlist from the DataBase"""


class Advices(BasePlaylist):

    __slots__ = 'user'

    def __init__(self, user: discord.User | discord.Member, songs: list | None = None):
        super().__init__(f"{user.display_name}'s Advice List")
        self.user = user
        self.id = self.user.id
        self.songs = songs or []

    def add_song(self, song) -> None:
        with AdvicesCache() as cache:
            cache[str(self.id)]["songs"].append(song.id)
        super().add_song(song)

    def remove_song(self, song) -> None:
        with AdvicesCache() as cache:
            cache[str(self.id)]["songs"].remove(song.id)
        super().remove_song(song)

    @classmethod
    def from_database(cls, person: discord.User | discord.Member) -> 'Advices':
        
        from .song import PlaylistSong

        _songs: list[tuple[str | int, ...]] = []
        with AdvicesCache() as cache:
            song_ids = cache[str(person.id)]['songs']
        with Connector() as cur:
            for song_id in song_ids:
                cur.execute(f"SELECT * FROM Songs WHERE ID=?", (song_id,))
                _songs.append(cur.fetchone())
            songs = [PlaylistSong.from_database(song_info) for song_info in _songs if song_info != None]

        return cls(person, songs)

class LikedSongs(BasePlaylist):

    __slots__ = 'user'

    def __init__(self, user: discord.User | discord.Member, songs: list | None = None):
        super().__init__(f"{user.display_name}'s Advice List")
        self.user = user
        self.id = self.user.id
        self.songs = songs or []

    def add_song(self, song) -> None:
        with LikedSongsCache() as cache:
            cache[str(self.id)]["songs"].append(song.id)
        super().add_song(song)

    def remove_song(self, song) -> None:
        with LikedSongsCache() as cache:
            cache[str(self.id)]["songs"].remove(song.id)
        super().remove_song(song)

    @classmethod
    def from_database(cls, person: discord.User | discord.Member) -> 'LikedSongs':

        from .song import PlaylistSong

        _songs: list[tuple[str | int, ...]] = []
        with LikedSongsCache() as cache:
            if str(person.id) not in cache:
                cache[str(person.id)] = {
                    'songs': []
                }
            song_ids = cache[str(person.id)]['songs']
        with Connector() as cur:
            for song_id in song_ids:
                cur.execute(f"SELECT * FROM Songs WHERE ID=?", (song_id,))
                _songs.append(cur.fetchone())

            songs = [PlaylistSong.from_database(song_info) for song_info in _songs]

        return cls(person, songs)


class Playlist(BasePlaylist):

    __slots__ = (
        'author',
        'date',
        'guild',
        'password',
        'private',
    )

    guild: discord.Guild | discord.User | discord.Member

    def __init__(
        self,
        id: int,
        name: str,
        date: str,
        private: bool,
        password: str,
        author: discord.User | discord.Member,
        guild: discord.Guild | None
    ):

        super().__init__(name)

        self.id = id
        self.date = date
        self.author = author
        self.password = password
        self.private = private
        self.guild = guild or author 

    @staticmethod
    def __create_id(name: str) -> int:
        name = name.lower()
        return int(f'{len(name)}{printable.find(name[0])}{printable.find(name[round(len(name)/2)])}{printable.find(name[-1])}')
    
    def rename(self, name: str):
        self.name = name
        with Connector() as cur:
            cur.execute("""UPDATE Playlists
            SET Title=?
            WHERE ID=?;""",
            (self.name, self.id))

    def lock(self):
        self.private = True
        with Connector() as cur:
            cur.execute(f"""UPDATE Playlist
            SET Locked=1
            WHERE ID={self.id};""")

    def unlock(self):
        self.private = False
        with Connector() as cur:
            cur.execute(f"""UPDATE Playlist
            SET Locked=0
            WHERE ID={self.id};""")

    def set_password(self, password: str):
        self.password = password
        with Connector() as cur:
            cur.execute("""UPDATE Playlist
            SET Locked=1,
                Keyword=?
            WHERE ID=?;""",
            (password, self.id))

    def upload(self) -> None:
        with Connector() as cur:
            cur.execute(f"""INSERT INTO Playlists (ID, Title, Date, Locked, Keyword, Author, Guild) 
            VALUES ({self.id}, ?, ?, {self.private}, ?, ?, ?);""", (self.name, self.date, self.password, self.author.id, self.guild.id))
        with PlaylistCache() as cache:
            cache[str(self.id)]['songs'] = [song.id for song in self.songs]

    def delete(self) -> None:
        with Connector() as cur:
            cur.execute(f"DELETE FROM Playlists WHERE ID={self.id};")
        with PlaylistCache() as ps:
            del ps[str(self.id)]


    def add_song(self, song) -> None:
        with PlaylistCache() as cache:
            cache[str(self.id)]["songs"].append(song.id)
        super().add_song(song)

    def remove_song(self, song) -> None:
        with PlaylistCache() as cache:
            cache[str(self.id)]["songs"].remove(song.id)
        super().remove_song(song)
    
    @classmethod
    def new(cls, name: str, interaction: discord.Interaction, password: str) -> 'Playlist':
        return cls(
            id=cls.__create_id(name),
            name=name,
            date=datetime.datetime.now().strftime("%d/%m/%y"),
            private=(password != ''),
            password=password,
            author=interaction.user,
            guild=interaction.guild
        )

    @classmethod
    async def from_database(cls, interaction: discord.Interaction, reference: str) -> 'Playlist':

        from .song import PlaylistSong

        with Connector() as cur:
            cur.execute("SELECT * FROM Playlists WHERE Title=? AND (Guild=? OR Author=?);", (reference, interaction.guild.id, interaction.user.id)) # type: ignore
            playlist = cur.fetchone()

        kwargs = {
            'name': playlist[1],
            'interaction': interaction,
            'id': playlist[0],
            'password': playlist[3]
        }

        self = cls(**kwargs)
        self.author = await interaction.client.fetch_user(playlist[4])

        songs = []
        with PlaylistCache() as cache:
            for song_id in cache[str(self.id)]:
                songs.append(PlaylistSong.from_id(song_id))

        self.songs = songs

        return self

    @staticmethod
    async def from_person(person: discord.User | discord.Member) -> list[EmbeddablePlaylist]:
        with Connector() as cur:
            cur.execute("SELECT * FROM Playlists WHERE Author=?;", (person.id,))
            playlists = cur.fetchall()

        embeddable = []
        for playlist in playlists:
            embeddable.append(EmbeddablePlaylist(
                playlist[1],
                playlist[2]
            ))
        
        return embeddable

    def from_youtube(self, info: dict[str, Any]) -> None:
        from .song import PlaylistSong

        for entry in info['entries']:
            self.add_song(PlaylistSong.from_youtube(entry))

    @classmethod
    def existing(cls, interaction: discord.Interaction, name: str) -> bool:
        with Connector() as cur:
            cur.execute(f"SELECT * FROM Playlists WHERE Title=? AND (Guild=? OR Author=?);", (name, interaction.guild.id, interaction.user.id)) # type: ignore
            playlist = cur.fetchone()

        return bool(playlist)
