from string import printable
from typing import Any
from typing_extensions import Self

import discord
import resources.connections as conn

from .base import Playlist as BasePlaylist
from models.songs import Song
from resources import Time, USER


__all__ = ("Playlist",)


class Playlist(BasePlaylist):

    __slots__ = (
        "author",
        "date",
        "guild",
        "password",
        "private",
    )

    guild: discord.Guild | USER

    cache = conn.PlaylistCache

    def __init__(
        self,
        id: int,
        name: str,
        date: str,
        private: bool,
        password: str,
        author: USER,
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
    def __create_id(name: str, author: discord.User | discord.Member) -> int:
        name = name.lower()
        first = f"{len(name)}{printable.find(name[0])}{printable.find(name[round(len(name)/2)])}{printable.find(name[-1])}"
        
        auth_id = str(author.id)
        last = f"{auth_id[0]}{auth_id[round(len(auth_id)/2)]}{auth_id[-1]}"
        
        return int(f"{first}{last}")
    
    def rename(self, name: str):
        self.name = name
        with conn.Connector() as cur:
            cur.execute("UPDATE Playlists SET Title=? WHERE ID=?;", (self.name, self.id))

    def lock(self):
        self.private = True
        with conn.Connector() as cur:
            cur.execute("UPDATE Playlist SET Locked=1 WHERE ID=?;", (self.id,))

    def unlock(self):
        self.private = False
        with conn.Connector() as cur:
            cur.execute("UPDATE Playlist SET Locked=0 WHERE ID=?;", (self.id,))

    def set_password(self, password: str):
        self.password = password
        with conn.Connector() as cur:
            cur.execute("UPDATE Playlist SET Locked=1, Keyword=? WHERE ID=?;", (password, self.id))

    def upload(self) -> None:
        with conn.Connector() as cur:
            cur.execute("""INSERT INTO Playlists (ID, Title, Date, Locked, Keyword, Author, Guild) 
            VALUES (?, ?, ?, ?, ?, ?, ?);""", 
            (self.id, self.name, self.date, self.private, self.password, self.author.id, self.guild.id))
        with self.cache() as cache:
            cache[str(self.id)]["songs"] = [song.data.id for song in self]

    def delete(self) -> None:
        with conn.Connector() as cur:
            cur.execute(f"DELETE FROM Playlists WHERE ID=?;", (self.id,))
        with self.cache() as ps:
            del ps[str(self.id)]


    def add_song(self, song: Song) -> None:
        with self.cache() as cache:
            cache[str(self.id)]["songs"].append(song.data.id)
        super().add_song(song)

    def remove_song(self, song: Song) -> None:
        with self.cache() as cache:
            cache[str(self.id)]["songs"].remove(song.data.id)
        super().remove_song(song)
    
    @classmethod
    def new(cls, name: str, interaction: discord.Interaction, password: str) -> Self:
        return cls(
            id=cls.__create_id(name, interaction.user),
            name=name,
            date=Time.today(),
            private=(password != ""),
            password=password,
            author=interaction.user,
            guild=interaction.guild
        )

    @classmethod
    async def from_database(cls, interaction: discord.Interaction, reference: str) -> Self:
        with conn.Connector() as cur:
            cur.execute("SELECT * FROM Playlists WHERE Title=? AND (Guild=? OR Author=?);", (reference, interaction.guild.id, interaction.user.id)) # type: ignore
            playlist = cur.fetchone()

        self = cls(*playlist)
        self.author = await interaction.client.fetch_user(playlist[4])
        self.guild = await interaction.client.fetch_guild(playlist[5])

        with cls.cache() as cache:
            for song_id in cache[str(self.id)]:
                self.append(Song.from_id(song_id))

        return self

    # @staticmethod
    # async def from_person(person: discord.User | discord.Member) -> list[EmbeddablePlaylist]:
    #     with conn.Connector() as cur:
    #         cur.execute("SELECT * FROM Playlists WHERE Author=?;", (person.id,))
    #         playlists = cur.fetchall()

    #     embeddable = []
    #     for playlist in playlists:
    #         embeddable.append(EmbeddablePlaylist(
    #             playlist[1],
    #             playlist[2]
    #         ))
        
    #     return embeddable
    # TODO: Either remove or use somehow

    def from_youtube(self, info: dict[str, Any]) -> None:
        for entry in info["entries"]:
            self.add_song(Song.from_youtube(entry))

    @classmethod
    def existing(cls, interaction: discord.Interaction, name: str) -> bool:
        with conn.Connector() as cur:
            cur.execute(f"SELECT * FROM Playlists WHERE Title=? AND (Guild=? OR Author=?);", (name, interaction.guild.id, interaction.user.id)) # type: ignore
            playlist = cur.fetchone()

        return bool(playlist)
