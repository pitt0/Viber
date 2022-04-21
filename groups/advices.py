from discord import app_commands as slash
# from discord.ext import tasks

import discord
# import random
import resources as res


class AdviceList(slash.Group):

    def __init__(self, client: discord.Client):
        super().__init__()
        self.client = client

    # @tasks.loop(hours=24)
    # # TODO: Set personalyzed timers
    # async def reminder(self):
    #     ppl: set[discord.Member | discord.User] = set()
    #     for guild in self.client.guilds:
    #         for member in guild.members:
    #             if not member.bot: ppl.add(member)

    #     for member in ppl:
    #         advicelist = res.Advices.from_database(member)
    #         if advicelist is None:
    #             continue
    #         song = random.choice(advicelist.songs)
    #         embed = discord.Embed(
    #             title=song.title, 
    #             description=f"Hey {member.name}! Someone adviced you this song by {song.artist}. Why don't you try to listen to it?"
    #             )
    #         embed.set_image(url=song.thumbnail)
    #         # TODO: Add a snooze/dismiss button
    #         await member.send(embed=embed)

    @slash.command(name='advice', description='Advice a song to someone in this server.')
    @slash.describe(reference='A reference to the song you want to advice', person='The person you want to advice the song.')
    async def advice_song(self, interaction: discord.Interaction, reference: str, person: discord.Member):
        interaction.namespace

        song = await res.Song.from_data(reference, interaction)
        if song is None:
            return
        res.Advices.advice_song(song, person)


    @slash.command(name='my_advices', description='Send your Advice List.')
    async def advice_list(self, interaction: discord.Interaction):
        embeds: list[discord.Embed]
        
        embed = discord.Embed(title='Your Advice List', color=discord.Color.og_blurple())

        AdviceList = res.Advices.from_database(interaction.user)
        if AdviceList is None:
            embed.description = 'Empty'
            embeds = [embed]

        else:
            if len(AdviceList.songs) < 10:
                embeds = [embed]
            else:
                embeds = []
                embed.description = f'{len(AdviceList.songs)} songs'
                for i in range(len(AdviceList.songs)):
                    if (i + 1)//10 == 0:
                        embeds.append(discord.Embed(title=f'Page { i + 1 }', description=f'{len(AdviceList.songs)} songs', color=discord.Color.og_blurple()))
                        
                for index, song in enumerate(AdviceList.songs):
                    currEmbed = embeds[(index + 1)//10]
                    currEmbed.add_field(name=song.title, value=f'{song.artist} • {song.album}', inline=False)

        if len(embeds) == 1:
            await interaction.response.send_message(embed=embeds[0])
        else:
            await interaction.response.send_message(embed=embeds[0], view=res.VAdviceList(embeds))
