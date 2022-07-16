from discord import app_commands as slash
# from discord.ext import tasks

import discord

# import random
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


