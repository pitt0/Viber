import discord
from .missing import MISSING
from typing import Protocol


__all__ = (
    'Embedder',

    'Paginator',
    'Queuer',
    'Slider'
)



def round_up(num: float) -> int:
    if num == int(num):
        return int(num)
    return int(num) + 1


class Embedder(Protocol):

    def get_current(self) -> discord.Embed:
        ...


class Queuer[T](Embedder):
    
    def __init__(self, title: str, elements: list[T], name: str, value: str, colour: discord.Colour = MISSING) -> None:
        self.elements = elements

        self.title = title
        self.colour = colour

        self.__name = name
        self.__value = value

        self.__receipts: list[discord.Embed | None] = [None for _ in range(self.receipts)]

    @property
    def receipts(self) -> int:
        return round_up(len(self.elements) / 5)
    
    def add_element(self, element: T) -> None:
        self.elements.append(element)
    
    def remove_element(self, receipt: int, element: int) -> T:
        return self.elements.pop(receipt * 6 + element)

    def get_current(self, index: int) -> discord.Embed:
        if self.__receipts[index] is not None:
            return self.__receipts[index] # type: ignore[non-null]
        
        considering = self.__receipts[(index - 1) * 6: index * 6]
        receipt = discord.Embed(
            title=self.title,
            colour=self.colour
        )

        for element in considering:
            receipt.add_field(name=element.__getattribute__(self.__name), value=element.__getattribute__(self.__value), inline=False)
        self.__receipts[index] = receipt
        return receipt


class Slider(Embedder): 

    def __init__(self) -> None:
        super().__init__()

    def get_current(self) -> discord.Embed:
        return super().get_current()


class Paginator[T](Embedder):

    def __init__(
            self, 
            title: str, 
            elements: list[T], 
            name: str, 
            value: str,
            colour: discord.Colour = MISSING, 
            description: str = MISSING,
            dynamic: bool = False
    ) -> None:
        self.elements = elements

        self.title = title
        self.description = description or f'Page [page] of {self.pages}'
        self.colour = colour

        self.__name = name
        self.__value = value

        self.__dynamic = dynamic
        self.__pages: list[discord.Embed | None] = [None for _ in range(self.pages)]

    @property
    def pages(self) -> int:
        return round_up((len(self.elements) / 12) + 1)
    
    def remove_element(self, page: int, index: int) -> T:
        return self.elements.pop(page * 13 + index)
    
    def get_current(self, index: int) -> discord.Embed:
        if self.__pages[index] is not None:
            return self.__pages[index] # type: ignore[non-null]
        
        considering = self.elements[(index - 1) * 13: index * 13] # NOTE: slices won't rise an error even if the latter value exceeds list's length 
        page = discord.Embed(
            title=self.title,
            description=self.description,
            colour=self.colour
        )

        for element in considering:
            page.add_field(name=element.__getattribute__(self.__name), value=element.__getattribute__(self.__value))
        if not self.__dynamic:
            self.__pages[index] = page
        return page
