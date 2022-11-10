from abc import abstractclassmethod
from typing_extensions import Self

import discord

from .song import Song


__all__ = ("Playlist",)


class Playlist(list[Song]):
    
    __slots__ = (
        "name",
        "id"
    )

    id: int
    
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, self.__class__) and __o.id == self.id

    def __ne__(self, __o: object) -> bool:
        return not self.__eq__(__o)

    def __str__(self) -> str:
        return f"{self.name}#{self.id}"

    def __create_embed(self, page: int) -> discord.Embed:
        if hasattr(self, "user"):
            target = self.user # type: ignore
        else:
            target = self.author # type: ignore
        _e = discord.Embed(
            title=self.name,
            description=f"by {target.display_name}",
            color=discord.Color.blurple()
        )
        _e.set_footer(text=f"Page {page}")
        return _e


    @property
    def empty(self) -> bool:
        return len(self) == 0

    @property
    def embeds(self) -> list[discord.Embed]:
        es: list[discord.Embed] = []
        
        for index, song in enumerate(self):
            page = (index // 12) + 1

            if page > len(es):
                es.append(self.__create_embed(page))
            
            current = es[-1]
            current.add_field(name=song.title, value=f"{song.author} • {song.album}", inline=True)
        
        return es

    def add_song(self, song) -> None:
        self.append(song)

    def remove_song(self, song) -> None:
        self.remove(song)
        
    @abstractclassmethod
    def from_database(cls, _) -> Self | None:
        """Retrives the Playlist from the DataBase"""