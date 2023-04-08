from list_ext import List, LoopingList
from typing import Any
from typing import overload

import discord
import random

from models.songs import Track
from models.typing import USER


SONG_ENTRY = tuple[Track, discord.FFmpegOpusAudio, USER]

class Queue(LoopingList[SONG_ENTRY]):

    index: int

    loop: int

    def __init__(self) -> None:
        super().__init__()

        self.loop = 0
        self.index = 0

    @property
    def left(self) -> List[SONG_ENTRY]:
        return List(self[self.index :])

    @property
    def looping(self) -> bool:
        return self.loop > 0

    @property
    def embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="Queue",
            color=discord.Color.orange()
        )
        for song, _, _ in self.left:
            embed.add_field(**song.as_field)
        
        return embed

    @property
    def song_loop(self) -> bool:
        return self.loop == 2

    @overload
    def __getitem__(self, key: int) -> SONG_ENTRY:
        ...
    
    @overload
    def __getitem__(self, key: slice) -> list[SONG_ENTRY]:
        ...

    def __getitem__(self, key) -> Any:
        if isinstance(key, int):
            if self.loop:
                if self.index > self.capacity:
                    key -= self.capacity
            return self[key]

        return self[key]


    def previous(self) -> None:
        if not self.song_loop:
            self.index -= 1

    @property
    def current(self) -> SONG_ENTRY:
        return self[self.index]

    def next(self) -> None:
        if not self.song_loop:
            self.index += 1

    def shuffle(self) -> None:
        copy = self[self.index + 1 : ]
        random.shuffle(copy)
        self[self.index + 1 : ] = copy

    def how_long(self) -> int:
        """Returns how many songs are left to play.
        """
        return self.capacity - self.index

    def can_shuffle(self) -> bool:
        return self.how_long() > 1

    def can_previous(self) -> bool:
        return self.index > 0

    def can_next(self) -> bool:
        return self.index < self.capacity and not self.song_loop

    def done(self) -> bool:
        return not self.looping and self.index == self.length
