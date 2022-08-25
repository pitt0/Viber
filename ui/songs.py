from typing import TYPE_CHECKING
import discord

if TYPE_CHECKING:
    from models import (
        AdviceableSong,
        ChoosableSong
        )




class VChoosableSong(discord.ui.View):

    def __init__(self, songs: list['ChoosableSong']):
        super().__init__()
        self.songs = songs
        self.current_song: 'ChoosableSong' = self.songs[0]
        self.index = 0

    @property
    def index(self) -> int:
        return self.__index

    @index.setter
    def index(self, value: int):
        assert (0 <= value <= len(self.songs) - 1), f'Value set for index: {value}'

        self.current_song = self.songs[value]

        self._to_first.disabled = self.back.disabled = (value == 0)
        self.forward.disabled = self._to_last.disabled = (value == len(self.songs) -1)

        self.__index = value

    @discord.ui.button(label='<<')
    async def _to_first(self, interaction: discord.Interaction, _):
        self.index = 0

        await interaction.response.edit_message(embed=self.current_song.embed, view=self)

    @discord.ui.button(label='<')
    async def back(self, interaction: discord.Interaction, _):
        self.index -= 1

        await interaction.response.edit_message(embed=self.current_song.embed, view=self)

    @discord.ui.button(label='>')
    async def forward(self, interaction: discord.Interaction, _):
        self.index += 1

        await interaction.response.edit_message(embed=self.current_song.embed, view=self)

    @discord.ui.button(label='>>')
    async def _to_last(self, interaction: discord.Interaction, _):
        self.index = len(self.songs) - 1

        await interaction.response.edit_message(embed=self.current_song.embed, view=self)

    @discord.ui.button(label='✓', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, _):
        await interaction.response.defer()
        try:
            await interaction.message.delete() # type: ignore
        except discord.NotFound:
            print('message not found')
        self.stop()

class VAdviceableSong(discord.ui.View):

    def __init__(self, song: 'AdviceableSong'):
        super().__init__()
        self.song = song

    @discord.ui.button(emoji='💟')
    async def like_song(self, interaction: discord.Interaction, _) -> None:
        pass