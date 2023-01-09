from typing import Type, TypeVar

import discord

from models.songs import Song, LyricsSong
from models.utils import NotFound
from models.utils import spotify as sp
from models.utils import youtube as yt
from ui import MenuView


__all__ = ("SongsChoice",)


class SongsChoice(list[Song]):

    reference: str

    def __init__(self, reference: str, purpose: Type[Song | LyricsSong]):
        tracks = sp.search(reference)
        if (len(tracks) == 0):
            tracks = yt.search_infos(reference)
            
        for track in tracks:
            self.append(purpose.as_choice(track))

    @property
    def empty(self) -> bool:
        return len(self) == 0

    @property
    def first(self) -> Song:
        return self[0]

    @property
    def countable(self) -> bool:
        return len(self) > 1

    @classmethod
    def search(cls, reference: str, purpose: Type[Song | LyricsSong]):
        self = cls(reference, purpose)
        if self.empty:
            # It's ok for the moment, if error tracking does not work:
            # use `if self.empty` out of this method
            raise NotFound(f"Searching `{reference}` returned no result.")
        return self


    async def choose(self, interaction: discord.Interaction) -> Song | LyricsSong:
        view = VSongsChoice(self)
        await interaction.response.send_message(embed=self.first.embed, view=view)
        await view.wait()
        view.song.cache(self.reference)
        return view.song



class VSongsChoice(MenuView):

    def __init__(self, songs: SongsChoice):
        embeds = []
        for song in songs:
            embeds.append(song.embed)
        super().__init__(embeds)
        self.songs = songs
        self.current = songs.first.embed
        self.index = 0

    @discord.ui.button(label="✓", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, _):
        await interaction.response.defer()
        self.song = self.songs[self.index]
        try:
            await interaction.message.delete() # type: ignore
        except discord.NotFound:
            print("message not found")
        self.stop()