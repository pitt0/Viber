import asyncio
import datetime
import discord

from api.local import reminders
from discord import app_commands as slash
from discord.ext import tasks


class Reminder(slash.Group):

    def __init__(self, client: discord.Client) -> None:
        super().__init__()
        self.client = client
        self.remind.start()

    @tasks.loop(hours=24)
    async def remind(self) -> None:
        rems = reminders.get()
        for reminder in rems:
            adviser_id = reminder.prepare()
            user = await self.client.fetch_user(reminder.person_id)
            adviser = await self.client.fetch_user(adviser_id)
            if not reminder.is_to_remind():
                await asyncio.sleep(reminder.delay)
            await user.send(embed=reminder.embed(user, adviser)) # TODO: Add a view
            reminder.sent()

    # @slash.command(name="")
    # async def foo(self, interaction: discord.Interaction) -> None:
    #     ...