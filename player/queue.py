import random
from typing import Any, overload

import discord

from models.songs import Song
from resources import Queuer
from typings import User

SONG_ENTRY = tuple[Song, User]


class Queue(list[SONG_ENTRY]):

    _index: int

    loop: int

    def __init__(self) -> None:
        super().__init__()

        self.queuer = Queuer[Song](
            "Queue", [], "title", "artists", discord.Colour.orange()
        )

        self.loop = 0
        self._index = 0

    @property
    def left(self) -> list[SONG_ENTRY]:
        return list(self[self._index :])

    @property
    def looping(self) -> bool:
        return self.loop > 0

    @property
    def embed(self) -> discord.Embed:
        return self.queuer.get_current(self._index)

    @property
    def song_loop(self) -> bool:
        return self.loop == 2

    @property
    def capacity(self) -> int:
        return len(self) - 1

    @overload
    def __getitem__(self, key: int) -> SONG_ENTRY: ...

    @overload
    def __getitem__(self, key: slice) -> list[SONG_ENTRY]: ...

    def __getitem__(self, key) -> Any:
        if isinstance(key, int):
            if self.loop:
                while self._index > self.capacity:
                    key -= self.capacity

        return super().__getitem__(key)

    def append(self, entry: SONG_ENTRY) -> None:
        self.queuer.add_element(entry[0])
        super().append(entry)

    def previous(self) -> None:
        if not self.song_loop:
            self._index -= 1

    @property
    def current(self) -> SONG_ENTRY:
        return self[self._index]

    def next(self) -> None:
        if not self.song_loop:
            self._index += 1

    def shuffle(self) -> None:
        copy = self[self._index + 1 :]
        random.shuffle(copy)
        self[self._index + 1 :] = copy

    def how_long(self) -> int:
        """Returns how many songs are left to play."""
        return self.capacity - self._index

    def can_shuffle(self) -> bool:
        return self.how_long() > 1

    def can_previous(self) -> bool:
        return self._index > 0

    def can_next(self) -> bool:
        return self._index < self.capacity and not self.song_loop

    def done(self) -> bool:
        return not self.looping and self._index == len(self)
