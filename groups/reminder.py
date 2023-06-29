import api.queries as queries
import asyncio
import datetime
import dateutil.parser as dparser
import discord

from api.local import reminders
from discord import app_commands as slash
from discord.ext import tasks
from enum import Enum


class Weekday(Enum):
    Daily = -1
    Mon = 0
    Tue = 1
    Wed = 2
    Thu = 3
    Fri = 4
    Sat = 5
    Sun = 6


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


    @slash.command(name='enable', description='Sets reminders on')
    async def enable(self, interaction: discord.Interaction) -> None:
        if queries.check('SELECT active FROM reminders WHERE person_id = ?;', (interaction.user.id)):
            await interaction.response.send_message('Reminders are already on.')
            return 
        queries.write('UPDATE reminders SET active = 1 WHERE person_id = ?;', (interaction.user.id))
        await interaction.response.send_message('Reminders set on!')


    @slash.command(name='disable', description='Sets reminders off')
    async def disable(self, interaction: discord.Interaction) -> None:
        if not queries.check('SELECT active FROM reminders WHERE person_id = ?;', (interaction.user.id)):
            await interaction.response.send_message('Reminders are already off.')
            return 
        queries.write('UPDATE reminders SET active = 0 WHERE person_id = ?;', (interaction.user.id))
        await interaction.response.send_message('Reminders set off!')


    @slash.command(name='weekday', description='Choose when to recieve the notification (day)')
    async def set_weekday(self, interaction: discord.Interaction, weekday: Weekday) -> None:
        queries.write('UPDATE reminders SET weekday = ? WHERE person_id = ?;', (weekday.value, interaction.user.id))
        await interaction.response.send_message('Done! Weekday set correctly.')


    @slash.command(name='time', description='Choose when to recieve the notification (time)')
    async def set_time(self, interaction: discord.Interaction, time: str) -> None:
        try:
            _time = dparser.parse(time)
            if _time.date() != datetime.date.today():
                raise ValueError

        except (ValueError, dparser.ParserError):
            await interaction.response.send_message('Incorrect value set for time. Notification time left unchanged.')
            return
        
        time = _time.strftime('%H:%M')
        queries.write('UPDATE reminders SET remind_time = ? WHERE person_id = ?;', (time, interaction.user.id))
        await interaction.response.send_message(f'Notification time correctly set to `{time}`!')