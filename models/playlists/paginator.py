import discord
from abc import ABC, abstractmethod
from models.typing import Field
from typing import Callable, TypeVar


T = TypeVar('T')


class Paginator(ABC, list[T]):

    title: str

    @property
    def pages(self) -> int:
        return (len(self)//12)+1

    def empty_embed(self) -> discord.Embed:
        return discord.Embed(
            title=self.title,
            description="There's nothing in here :("
        )

    @abstractmethod
    def paginate(self, page) -> discord.Embed:
        ...

    def embeds(self, field: Callable[[T], Field]) -> list[discord.Embed]:
        if len(self) == 0:
            return [self.empty_embed()]
        
        pages: list[discord.Embed] = []

        for index, item in enumerate(self): 
            page = (index // 12) + 1

            if page > len(pages):
                pages.append(self.paginate(page))

            pages[-1].add_field(**field(item))

        return pages