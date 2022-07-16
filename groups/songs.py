from discord import app_commands as slash

import discord
import json

from connections import SongCache
from models import Advices, Song
from models import song as songs

class Songs(slash.Group):
    
    @slash.command(name='advice', description='Advices a song to someone in this server')
    async def advice_song(self, interaction: discord.Interaction, song: str, to: discord.Member) -> None:
        await interaction.response.defer()

        song_id: str | int

        with SongCache() as cache:
            song_id = cache.get(song) # type: ignore
        
        if song_id is not None:
            _song = Song.from_id(song_id)
        else:        
            _song = await songs.choose(interaction, song)
            song_id = _song.id

        advices = Advices.from_database(to)
            
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
        pass