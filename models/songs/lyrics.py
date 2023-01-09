import discord

from .base import Song, SongData
from models.utils import genius

class LyricsSong(Song):

    lyrics: str

    def __init__(self, data: SongData):
        super().__init__(data)

        self.lyrics = genius.lyrics(self) or "Could not find anything :("
        # Lyrics searching is really heavy as a process
        # so I decided to separate this class from the super
        # since it's only needed in one context

    def switch(self) -> discord.Embed:
        if self.embed.description == self.lyrics:
            self.embed.description = f"{self.data.author} • {self.data.album}"
            self.embed.add_field(name="Duration", value=self.data.duration)
            self.embed.add_field(name="Year", value=self.data.year)
        else:
            self.embed.description = self.lyrics
            self.embed.clear_fields()
        
        return self.embed
