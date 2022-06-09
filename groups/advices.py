from discord import app_commands as slash
# from discord.ext import tasks

import discord
# import random
import ui

from models import Advices

# ADVICES = [
#     "Remember to listen to *song_title* by *song_author*. Someone adviced you this song and I think they would really like if you'd do that.",
#     "Someone adviced you *song_title* by *song_author*. Why don't you try to listen to it?"
# ]

class AdviceList(slash.Group):

    def __init__(self, client: discord.Client):
        super().__init__()
        self.client = client

    # @tasks.loop(hours=24 * 7)
    # # TODO: Set personalyzed timers
    # async def reminder(self):
    #     ppl: set[discord.Member | discord.User] = set()
    #     for guild in self.client.guilds:
    #         for member in guild.members:
    #             if not member.bot: ppl.add(member)

    #     for member in ppl:
    #         advicelist = Advices.from_database(member)
    #         if advicelist.empty:
    #             continue
    #         song = random.choice(advicelist.songs)
    #         embed = discord.Embed(
    #             title=f'Hey {member.name}!',
    #             description=random.choice(ADVICES).replace('*song_title*', song.title).replace('*song_author*', song.author)
    #             )
    #         embed.set_image(url=song.thumbnail)
    #         # TODO: Add a snooze/dismiss button
    #         await member.send(embed=embed)

    @slash.command(name='advice', description='Advice a song to someone in this server.')
    @slash.describe(reference='A reference to the song you want to advice', person='The person you want to advice the song.')
    async def advice_song(self, interaction: discord.Interaction, reference: str, person: discord.Member):
        song = await ui.choose(interaction, reference)
        if song is None:
            return

        advices = Advices.from_database(person)
        if song in advices:
            await interaction.followup.send(f"This song is already in {person.display_name}'s advice list", ephemeral=True)
            return
        advices.add_song(song)
        await interaction.followup.send(f"`{song.title} • {song.author}` adviced to {person.mention}")


    @slash.command(name='my_advices', description='Send your Advice List.')
    async def advice_list(self, interaction: discord.Interaction):
        advices = Advices.from_database(interaction.user)
        await interaction.response.send_message(embed=advices.embeds[0], view=ui.MenuView(advices.embeds))
