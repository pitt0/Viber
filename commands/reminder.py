# import asyncio
import datetime
import dateutil.parser as dparser
import discord

from api.connections import ReminderCache
from api.local import ReminderAPI, SongsAPI
from discord import app_commands as slash
from discord.ext import tasks, commands
from enum import Enum
from resources import Time
from ui import ReminderOptions


class Weekday(Enum):
    Daily = -1
    Mon = 0
    Tue = 1
    Wed = 2
    Thu = 3
    Fri = 4
    Sat = 5
    Sun = 6


class Reminder(commands.GroupCog):

    def __init__(self, client: discord.Client) -> None:
        self.client = client
        self.remind.start()

    async def _find_user(self, user_id: int) -> discord.User | None:
        try:
            return await self.client.fetch_user(user_id)
        except discord.NotFound:
            return None

    @tasks.loop(hours=24)
    async def remind(self) -> None:
        timers = await ReminderAPI.get_timers()
        for timer in timers:
            print(f'[{Time.now()}] Timer starting')
            await timer.start()
            print(f'[{Time.now()}] Timer finished')

            reminder = await ReminderAPI.get_reminder(timer.playlist_id)
            song = await SongsAPI.get_song(reminder.song_id)

            if (user := await self._find_user(reminder.user_id)) is None:
                # TODO - remove user from database
                continue

            _embed = discord.Embed(
                title=f'Hey {user.display_name}, check this out!',
                description=song,
                colour=discord.Colour.orange()
            )
            _embed.set_image(url=song.thumbnail)
            if (adviser := await self._find_user(reminder.adviser_id)) is not None:
                _embed.set_footer(text=f"Advised by {adviser.display_name}", icon_url=adviser.display_avatar)

            ReminderCache.add(user.id, song)
            view = ReminderOptions(user, song) # TODO: edit
            await user.send(embed=song.embed, view=view)



    @slash.command(name='enable', description='Sets reminders on')
    async def enable(self, interaction: discord.Interaction) -> None:
        # TODO - if someone enables this after the task loads timers, the reminder will not be sent, resolve
        if (notification := ReminderAPI.check_active(interaction.user.id)) is None:
            await interaction.response.send_message("You are not registered in the database")
            return
        if notification:
            await interaction.response.send_message('Reminders are already on.')
            return 
        queries.write('UPDATE reminders SET active = 1 WHERE person_id = ?;', (interaction.user.id,))
        await interaction.response.send_message('Reminders set on!')


    @slash.command(name='disable', description='Sets reminders off')
    async def disable(self, interaction: discord.Interaction) -> None:
        if not ReminderAPI.check_active(interaction.user.id):
            await interaction.response.send_message('Reminders are already off.')
            return 
        queries.write('UPDATE reminders SET active = 0 WHERE person_id = ?;', (interaction.user.id,))
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
