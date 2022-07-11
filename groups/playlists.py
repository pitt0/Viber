from discord import app_commands as slash
from discord.ui import TextInput

import discord
import json

import ui
import models.utils.youtube as yt
from models import Playlist, Song
from models.utils.errors import WrongLink



with open('database/playlist_cache.json') as f:
    cached_playlists: dict[str, dict[str, int]] = json.load(f)

def create_playlist(name: str, interaction: discord.Interaction, password: str | None = None) -> Playlist:
    return Playlist(name, interaction, password=password) # type: ignore

async def autocomplete(interaction: discord.Interaction, current: str) -> list[slash.Choice[str]]:
    return [
        slash.Choice(name=playlist, value=playlist) 
        for playlist, data in cached_playlists.items() 
        if (data['guild'] == interaction.guild.id or data['author'] == interaction.user.id) and current.lower() in playlist.lower() # type: ignore
        ] 



class MNewPlaylist(discord.ui.Modal, title='Create a Playlist'):
    
    name = TextInput(label='Playlist Title', placeholder='Title', required=False, min_length=2, max_length=20)
    password = TextInput(label='Playlist Password Leave Empty to Keep it Free', placeholder='Password', required=False, min_length=8)
    url = TextInput(label='External Url', placeholder='Url', required=False, min_length=29)

    async def on_submit(self, interaction: discord.Interaction):
        if self.name is None and self.url is None:
            raise WrongLink()
        
        songs = []
        info = {}
        if self.url is not None:
            info = yt.from_link(self.url) # type: ignore
            self.name = info['title']

        if Playlist.existing(interaction, str(self.name)):
            await interaction.response.send_message('This playlist already exists!', ephemeral=True)
            return
            
        playlist = create_playlist(str(self.name), interaction, str(self.password))
        playlist.upload()
        await interaction.response.send_message(f'Playlist `{playlist.name}#{playlist.id}` created.')

        for entry in info['entries']:
            songs.append(Song.from_youtube(entry))

        [playlist.add_song(song) for song in songs]
    
    async def on_error(self, error: Exception, interaction: discord.Interaction) -> None:
        if not isinstance(error, WrongLink):
            return await super().on_error(error, interaction)

        



class Playlists(slash.Group):

    @slash.command(name='new', description='Creates a playlist.')
    async def new_playlist(self, interaction: discord.Interaction) -> None:
        modal = MNewPlaylist()
        await interaction.response.send_modal(modal)
        
        global cached_playlists
        with open('database/playlist_cache.json') as f:
            cached_playlists = json.load(f)


    @slash.command(name='show', description='Shows a playlist. If the playlist is private it will be sent as a private message.')
    @slash.describe(name='The name of the playlist.')
    @slash.autocomplete(name=autocomplete)
    async def show_playlist(self, interaction: discord.Interaction, name: str) -> None:
        await interaction.response.defer()
        print(name)

        playlist = await Playlist.from_database(interaction, name) 
        print(playlist)     

        pView = ui.PlaylistPaginator(playlist)

        if playlist.private:
            await interaction.followup.send('The playlist has been sent you in DMs.')
            await interaction.user.send(embed=playlist.embeds[0], view=pView)
            return  

        await interaction.followup.send(embed=playlist.embeds[0], view=pView) 
