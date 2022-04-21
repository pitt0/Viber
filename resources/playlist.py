from abc import abstractclassmethod
from string import printable
from typing import TYPE_CHECKING, Optional

import discord

from .resources import IDENTIFIER

from .utils import Connector
from .song import Song


class BasePlaylist:
    
    __slots__ = (
        'name',
        'songs'
    )

    if TYPE_CHECKING:
        id: int
    
    def __init__(self, name: str):
        self.name = name

        self.songs: list[Song] = []


    def add_song(self, song: Song):
        self.songs.append(song)
        with Connector() as cur:
            cur.execute(f"INSERT INTO Songs (PlaylistID, SongID) VALUES ({self.id}, '{song.id}');")
        

    def remove_song(self, song: Song):
        self.songs.remove(song)
        with Connector() as cur:
            cur.execute(f"DELETE FROM Songs WHERE PlaylistID={self.id} AND SongID='{song.id}';")
        
    @abstractclassmethod
    def from_database(cls, reference) -> Optional['BasePlaylist']:
        """Retrives the Playlist from the DataBase"""





class Advices(BasePlaylist):

    __slots__ = 'user'

    def __init__(self, user: discord.User | discord.Member, songs: Optional[list[Song]] = None):
        super().__init__(f"{user.display_name}'s Advice List")
        self.user = user
        self.songs = songs or []

    @property
    def id(self) -> int:
        return self.user.id

    @classmethod
    def from_database(cls, reference: discord.User | discord.Member) -> Optional['Advices']:
        with Connector() as cur:
            cur.execute(f"SELECT * FROM Songs WHERE PlaylistID='{reference.id}'")
            _songs = cur.fetchall()

            songs = [Song.from_database(song_id[1]) for song_id in _songs]

        return cls(reference, songs)

    @staticmethod
    def advice_song(song: Song, person: discord.User | discord.Member) -> None:
        with Connector() as cur:
            cur.execute(f"INSERT INTO Songs (SongID, PlaylistID) VALUES ('{song.id}', '{person.id}')")





class Playlist(BasePlaylist):

    __slots__ = (
        'id',
        'author',
        'guild',
        'password',
        'private',

        '__from_db'
    )

    def __init__(
        self, 
        name: str, 
        author: discord.User | discord.Member,
        guild: discord.Guild,
        id: int | None = None,
        password: str | None = None,
        private: bool = False,
        from_db: bool = False
    ):

        super().__init__(name)

        self.id = id or self.__create_id(self.name)
        self.author = author
        self.password = password
        self.private = private
        self.guild = guild


        self.__from_db = from_db

    @staticmethod
    def __create_id(name: str) -> int:
        name = name.lower()
        return int(f'{len(name)}{printable.find(name[0])}{printable.find(name[round(len(name)/2)])}{printable.find(name[-1])}')


    def rename(self, name: str):
        self.name = name
        self.upload()

    def lock(self):
        self.private = True
        self.upload()

    def unlock(self):
        self.private = False
        self.upload()

    def upload(self) -> None:
        with Connector() as cur:
            if self.__from_db:
                cur.execute(f"DELETE FROM Playlists WHERE ID={self.id};")
            else:
                for song in self.songs:
                    cur.execute(f"INSERT INTO Songs (PlaylistID, SongID) VALUES ({self.id}, '{song.id}');")

            cur.execute(f"INSERT INTO Playlists (ID, Title, Locked, Keyword, Author, Guild) VALUES ({self.id}, %s, {self.private}, %s, '{self.author.id}', '{self.guild.id}');", (self.name, self.password))


    def delete(self) -> None:
        with Connector() as cur:
            cur.execute(f"DELETE FROM Playlists WHERE ID={self.id};")

    
    @classmethod
    def from_database(cls, guild: int, reference: IDENTIFIER) -> Optional['Playlist']:

        if isinstance(reference, str):
            id = cls.__create_id(reference)
        else: id = reference

        with Connector() as cur:
            cur.execute(f"SELECT * FROM Playlists WHERE ID=%s AND Guild='{guild}';", (id,))
            playlist = cur.fetchone()
            if playlist is None:
                return None
            
            cur.execute(f"SELECT * FROM Songs WHERE PlaylistID={playlist[0]};")
            _songs = cur.fetchall()
            songs = [Song.from_database(song_id[1]) for song_id in _songs]

        kwargs = {
            'name': playlist[1],
            'author': int(playlist[4]),
            'id': playlist[0],
            'password': playlist[3],
            'private': playlist[2],
            'guild': int(playlist[5])
        }
        
        Playlist = cls(from_db = True, **kwargs)
        Playlist.password = playlist[3]
        Playlist.songs = songs

        return Playlist

    
    @classmethod
    def existing(cls, guild: int, reference: IDENTIFIER) -> bool:
        if isinstance(reference, str):
            id = cls.__create_id(reference)
        else: id = reference
            

        with Connector() as cur:
            cur.execute(f"SELECT * FROM Playlists WHERE ID=%s AND Guild='{guild}';", (id,))
            playlist = cur.fetchall()

        return playlist != []