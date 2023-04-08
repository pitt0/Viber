from abc import ABC, abstractmethod
from typing import Callable, Iterable, TypeVar

import discord

from models.typing import Field


T = TypeVar('T')


class Paginator(ABC, Iterable[T]):

    @abstractmethod
    def paginate(self, page) -> discord.Embed:
        ...

    def embeds(self, field: Callable[[T], Field]) -> list[discord.Embed]:
        pages: list[discord.Embed] = []

        for index, item in enumerate(self): 
            page = (index // 12) + 1

            if page > len(pages):
                pages.append(self.paginate(page))

            pages[-1].add_field(**field(item))

        return pages