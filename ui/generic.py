import discord
from discord.utils import MISSING



class ResponseView(discord.ui.View):

    @property
    def current(self) -> discord.Embed:
        ...

    async def edit_or_respond(self, interaction: discord.Interaction, embed: discord.Embed = MISSING, view: discord.ui.View = MISSING) -> None:
        try:
            if interaction.response.is_done():
                await interaction.followup.edit_message(interaction.message.id, embed=(embed or self.current), view=(view or self)) # type: ignore[non-null]
            else:
                await interaction.response.edit_message(embed=(embed or self.current), view=(view or self))
        except discord.HTTPException:
            if interaction.response.is_done():
                await interaction.followup.send(embed=(embed or self.current), view=(view or self))
            else:
                await interaction.response.send_message(embed=(embed or self.current), view=(view or self))


class MenuView(ResponseView):

    def __init__(self, embeds: list[discord.Embed]) -> None:
        super().__init__()
        self.embeds = embeds

        self.index = 0

    @property
    def index(self) -> int:
        return self.__index

    @index.setter
    def index(self, value: int) -> None:
        assert (0 <= value <= len(self.embeds) - 1), f"Value set for index: {value}"

        self._to_first.disabled = self.back.disabled = not value
        self._to_last.disabled = self.forward.disabled = value == len(self.embeds) -1

        self.__index = value

    @property
    def current(self) -> discord.Embed:
        return self.embeds[self.index]

    
    @discord.ui.button(label="<<")
    async def _to_first(self, interaction: discord.Interaction, _) -> None:
        self.index = 0
        await self.edit_or_respond(interaction)

    @discord.ui.button(label="<")
    async def back(self, interaction: discord.Interaction, _) -> None:
        self.index -= 1
        await self.edit_or_respond(interaction)

    @discord.ui.button(label=">")
    async def forward(self, interaction: discord.Interaction, _) -> None:
        self.index += 1
        await self.edit_or_respond(interaction)

    @discord.ui.button(label=">>")
    async def _to_last(self, interaction: discord.Interaction, _) -> None:
        self.index = len(self.embeds) - 1
        await self.edit_or_respond(interaction)