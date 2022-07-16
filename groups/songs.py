from discord import app_commands as slash

import discord

from models import Advices, choose

class Songs(slash.Group):
    
    @slash.command(name='advice', description='Advices a song to someone in this server')
    async def advice_song(self, interaction: discord.Interaction, song: str, to: discord.Member) -> None:
        await interaction.response.defer()
        advices = Advices.from_database(to)
        _song = await choose(interaction, song)


        if _song not in advices.songs:
            advices.add_song(_song)
            message = f"`{_song.title} • {_song.author}` adviced to {to.mention}"
            ephemeral = False
        else:
            message = f"This song is already in {to.display_name}'s advice list"
            ephemeral = True

        await interaction.followup.send(message, ephemeral=ephemeral)

    @slash.command(name='search')
    async def search_song(self, interaction: discord.Interaction, song: str) -> None:
        await interaction.response.defer()
        _song = await choose(interaction, song)

        await interaction.followup.send(embed=_song.embed)