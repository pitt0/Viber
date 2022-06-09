from abc import abstractclassmethod
from string import printable
from typing import Optional

import discord
import json


from .utils import *
from .song import Song


class BasePlaylist:
    
    __slots__ = (
        'name',
        'songs',
        'id'
    )

    id: int
    
    def __init__(self, name: str):
        self.name = name

        self.songs: list[Song] = []

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, self.__class__) and __o.id == self.id

    def __iter__(self):
        return (song for song in self.songs)

    def __contains__(self, song: Song) -> bool:
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
        _e = self.__create_embed(1)
        es.append(_e)
        for index, song in enumerate(self.songs):
            if index%10 == 0:
                es.append(_e)
                _e = self.__create_embed(index//10)
            _e.add_field(name=song.title, value=f"{song.author} • {song.album}", inline=True)
        return es

    def add_song(self, song: Song) -> None:
        self.songs.append(song)
        song.upload(self.id)
        

    def remove_song(self, song: Song) -> None:
        self.songs.remove(song)
        song.remove(self.id)
        
    @abstractclassmethod
    def from_database(cls, reference) -> Optional['BasePlaylist']:
        """Retrives the Playlist from the DataBase"""



class Advices(BasePlaylist):

    __slots__ = 'user'

    def __init__(self, user: discord.User | discord.Member, songs: Optional[list[Song]] = None):
        super().__init__(f"{user.display_name}'s Advice List")
        self.user = user
        self.id = self.user.id
        self.songs = songs or []


    @classmethod
    def from_database(cls, person: discord.User | discord.Member) -> 'Advices':
        with Connector() as cur:
            cur.execute(f"SELECT * FROM Songs WHERE PlaylistID=?", (person.id,))
            _songs = cur.fetchall()

            songs = [Song.from_database(song_info) for song_info in _songs]

        return cls(person, songs)



class Playlist(BasePlaylist):

    __slots__ = (
        'author',
        'guild',
        'password',
        'private',
    )

    guild: discord.Guild | discord.User

    def __init__(
        self,
        name: str,
        interaction: discord.Interaction,
        id: int | None = None,
        password: str | None = None
    ):

        super().__init__(name)

        self.id = id or self.__create_id(self.name)
        self.author = interaction.user
        self.password = password
        self.private = bool(password)
        self.guild = interaction.guild or interaction.user # type: ignore

    @staticmethod
    def __create_id(name: str) -> int:
        name = name.lower()
        return int(f'{len(name)}{printable.find(name[0])}{printable.find(name[round(len(name)/2)])}{printable.find(name[-1])}')
    
    def rename(self, name: str):
        self.name = name
        self.update()

    def lock(self):
        self.private = True
        self.update()

    def unlock(self):
        self.private = False
        self.update()

    def set_password(self, password: str):
        self.password = password

    def upload(self) -> None:
        with Connector() as cur:
            cur.execute(f"""INSERT INTO Playlists (ID, Title, Locked, Keyword, Author, Guild) 
            VALUES ({self.id}, ?, {self.private}, ?, ?, ?);""", (self.name, self.password, self.author.id, self.guild.id))
        with PlaylistCacheReader() as ps:
            ps[self.name] = self.guild.id
        with PlaylistCacheEditor() as f:
            json.dump(ps, f, indent=4)

    def update(self) -> None:
        with Connector() as cur:
            cur.execute(f"""
            UPDATE TABLE Playlists
            SET Title='{self.name}',
                Author={self.author.id},
                Keyword='{self.password}',
                Locked={int(self.private)},
                Guild={self.guild.id}
            WHERE ID={self.id};
            """)


    def delete(self) -> None:
        with Connector() as cur:
            cur.execute(f"DELETE FROM Playlists WHERE ID={self.id};")
            cur.execute(f"DELETE FROM Songs WHERE PlaylistID={self.id};")
        with PlaylistCacheReader() as ps:
            del ps[self.name]
        with PlaylistCacheEditor() as f:
            json.dump(ps, f, indent=4)


    @classmethod
    async def from_database(cls, interaction: discord.Interaction, reference: str) -> 'Playlist':
        with Connector() as cur:
            cur.execute(f"SELECT * FROM Playlists WHERE Title=? AND Guild=? OR Author=?;", (reference, interaction.guild.id, interaction.user.id)) # type: ignore
            playlist = cur.fetchone()

            cur.execute(f"SELECT * FROM Songs WHERE PlaylistID={playlist[0]};")
            _songs: list[tuple[str | int, ...]] = cur.fetchall()
            songs = [Song.from_database(song_info) for song_info in _songs] # type: ignore

        kwargs = {
            'name': playlist[1],
            'interaction': interaction,
            'id': playlist[0],
            'password': playlist[3]
        }

        Playlist = cls(**kwargs)
        Playlist.author = await interaction.client.fetch_user(playlist[4])
        Playlist.songs = songs

        return Playlist


    @classmethod
    def existing(cls, interaction: discord.Interaction, name: str) -> bool:
        with Connector() as cur:
            cur.execute(f"SELECT * FROM Playlists WHERE Title=? AND Guild=? OR Author;", (name, interaction.guild.id, interaction.user.id)) # type: ignore
            playlist = cur.fetchall()

        return playlist != []