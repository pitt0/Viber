from discord.utils import MISSING

import asyncio
import discord



class MenuView(discord.ui.View):

    current: discord.Embed

    def __init__(self, embeds: list[discord.Embed]):
        super().__init__()
        self.embeds = embeds

        self.index = 0

    @property
    def index(self) -> int:
        return self.__index

    @index.setter
    def index(self, value: int):
        assert (0 <= value <= len(self.embeds) - 1), f"Value set for index: {value}"

        self.current = self.embeds[value]

        self._to_first.disabled = self.back.disabled = not value
        self._to_last.disabled = self.forward.disabled = value == len(self.embeds) -1

        self.__index = value

    async def respond(self, interaction: discord.Interaction, embed: discord.Embed = MISSING, view: discord.ui.View = MISSING):
        try:
            await interaction.response.edit_message(embed=(embed or self.current), view=(view or self))
        except discord.HTTPException:
            await interaction.response.send_message(embed=(embed or self.current), view=(view or self))

    @discord.ui.button(label="<<")
    async def _to_first(self, interaction: discord.Interaction, _):
        self.index = 0
        await self.respond(interaction)

    @discord.ui.button(label="<")
    async def back(self, interaction: discord.Interaction, _):
        self.index -= 1
        await self.respond(interaction)

    @discord.ui.button(label=">")
    async def forward(self, interaction: discord.Interaction, _):
        self.index += 1
        await self.respond(interaction)

    @discord.ui.button(label=">>")
    async def _to_last(self, interaction: discord.Interaction, _):
        self.index = len(self.embeds) - 1
        await self.respond(interaction)



class WaitableModal(discord.ui.Modal):

    def __init__(self, *, title: str = MISSING, timeout: float | None = None, custom_id: str = MISSING):
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)

        loop = asyncio.get_running_loop()
        self.__responded: asyncio.Future[bool] = loop.create_future()

    def stop(self):
        self.__responded.set_result(True)

    async def wait(self):
        await self.__responded