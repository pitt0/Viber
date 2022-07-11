from typing import TYPE_CHECKING
import discord

if TYPE_CHECKING:
    from models import Song




class VSong(discord.ui.View):

    children: list[discord.ui.Button]

    def __init__(self, songs: list['Song'], choice: bool = False):
        super().__init__()
        self.songs = songs
        self.current_song: 'Song' = self.songs[0]
        if not choice:
            self.remove_item(self.children[-1])
        self.index = 0

    @property
    def index(self) -> int:
        return self.__index

    @index.setter
    def index(self, value: int):
        assert (0 <= value <= len(self.songs) - 1), f'Value set for index: {value}'

        self.current_song = self.songs[value]
        print(self.songs[value].title)

        self.children[0].disabled = self.children[1].disabled = not value
        self.children[2].disabled = self.children[3].disabled = value == len(self.songs) -1

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
    async def fowrard(self, interaction: discord.Interaction, _):
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