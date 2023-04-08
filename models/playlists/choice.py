from list_ext import List
from typing import Self, Type

import discord

from models.songs import S
from models.errors import NotFound
from ui import MenuView


__all__ = ("SongsChoice",)


class SongsChoice(List[S]):

    reference: str

    def __init__(self, reference: str, purpose: Type[S], limit: int = 5) -> None:
        self.reference = reference
        tracks = purpose.search(reference, limit)
            
        super().__init__(purpose.create(track) for track in tracks) # NOTE: is it worth? should i do another class?

    @classmethod
    def search(cls, reference: str, purpose: Type[S], limit: int = 5) -> Self:
        self = cls(reference, purpose, limit)
        if self.empty:
            # It's ok for the moment, if error tracking does not work:
            # use `if self.empty` out of this method
            raise NotFound(f"Searching `{reference}` returned no result.")
        return self

    async def choose(self, interaction: discord.Interaction) -> S:
        view = VSongsChoice(self)
        if interaction.response.is_done():
            await interaction.followup.send(embed=self.first.embed, view=view)
        else:
            await interaction.response.send_message(embed=self.first.embed, view=view)
        await view.wait()
        return view.song



class VSongsChoice(MenuView):

    def __init__(self, songs: SongsChoice) -> None:
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