from list_ext import List
from typing import Type

import discord

from models.songs import Song, LyricsSong
from models.utils import NotFound
from models.utils import spotify as sp
from models.utils import youtube as yt
from ui import MenuView


__all__ = ("SongsChoice",)


class SongsChoice(List[Song]):

    reference: str

    def __init__(self, reference: str, purpose: Type[Song]):
        self.reference = reference
        tracks = sp.search(reference)
        if (len(tracks) == 0):
            tracks = yt.search_infos(reference)
            
        super().__init__(purpose.as_choice(track) for track in tracks)

    @classmethod
    def search(cls, reference: str, purpose: Type[Song]):
        self = cls(reference, purpose)
        if self.empty:
            # It's ok for the moment, if error tracking does not work:
            # use `if self.empty` out of this method
            raise NotFound(f"Searching `{reference}` returned no result.")
        return self


    async def choose(self, interaction: discord.Interaction) -> Song | LyricsSong:
        view = VSongsChoice(self)
        if interaction.response.is_done():
            await interaction.followup.send(embed=self.first.embed, view=view)
        else:
            await interaction.response.send_message(embed=self.first.embed, view=view)
        await view.wait()
        view.song.cache(self.reference)
        return view.song



class VSongsChoice(MenuView):

    def __init__(self, songs: SongsChoice):
        embeds = songs.select(lambda song: song.embed)
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