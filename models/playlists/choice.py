import discord

from models.songs import S, LocalSong
from resources import NotFound
from ui import MenuView
from typing import Self, Type


__all__ = ("SongsChoice",)


class SongsChoice(list[S]):

    reference: str

    def __init__(self, reference: str, purpose: Type[S], limit: int = 5) -> None:
        self.reference = reference
        tracks = purpose.search(reference, limit)
            
        super().__init__(purpose.create(track) for track in tracks) # NOTE: is it worth? should i do another class?

    @classmethod
    def search(cls, reference: str, purpose: Type[S], limit: int = 5) -> Self:
        self = cls(reference, purpose, limit)
        if not self:
            # It's ok for the moment, if error tracking does not work:
            # use `if self.empty` out of this method
            raise NotFound(f"Searching `{reference}` returned no result.")
        return self

    async def choose(self, interaction: discord.Interaction) -> LocalSong:
        view = VSongsChoice(self)
        if interaction.response.is_done():
            await interaction.followup.send(embed=self[0].embed, view=view)
        else:
            await interaction.response.send_message(embed=self[0].embed, view=view)
        await view.wait()
        return await view.song.dump()



class VSongsChoice(MenuView):

    def __init__(self, songs: SongsChoice[S]) -> None:
        embeds = [song.embed for song in songs]
        super().__init__(embeds)
        self.songs = songs
        self._current = songs[0].embed
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