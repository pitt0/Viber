import discord

class MenuView(discord.ui.View):

    children: list[discord.ui.Button]

    def __init__(self, embeds: list[discord.Embed]):
        super().__init__()
        self.embeds = embeds

        self.index = 0

    @property
    def index(self) -> int:
        return self.__index

    @index.setter
    def index(self, value: int):
        assert (0 <= value <= len(self.embeds) - 1), f'Value set for index: {value}'

        self.current_song = self.embeds[value]

        self.children[0].disabled = self.children[1].disabled = not value
        self.children[2].disabled = self.children[3].disabled = value == len(self.embeds) -1

        self.__index = value

    @discord.ui.button(label='<<')
    async def _to_first(self, interaction: discord.Interaction, _):
        self.index = 0

        await interaction.response.edit_message(embed=self.current_song, view=self)

    @discord.ui.button(label='<')
    async def back(self, interaction: discord.Interaction, _):
        self.index -= 1

        await interaction.response.edit_message(embed=self.current_song, view=self)

    @discord.ui.button(label='>')
    async def fowrard(self, interaction: discord.Interaction, _):
        self.index += 1

        await interaction.response.edit_message(embed=self.current_song, view=self)

    @discord.ui.button(label='>>')
    async def _to_last(self, interaction: discord.Interaction, _):
        self.index = len(self.embeds) - 1

        await interaction.response.edit_message(embed=self.current_song, view=self)
