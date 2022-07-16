from discord import app_commands as slash
from discord.ui import TextInput

import asyncio
import discord

import ui
import models.utils.youtube as yt
from models import Playlist, CachedPlaylist, Advices

# init cache
cached_playlists = CachedPlaylist.load()


async def autocomplete(interaction: discord.Interaction, current: str) -> list[slash.Choice[str]]:
    obj = []
    for playlist in cached_playlists:
        if playlist.showable(interaction) and playlist.is_input(current):
            obj.append(slash.Choice(name=playlist.name, value=playlist.name))
    return obj



class MNewPlaylist(discord.ui.Modal, title='Create a Playlist'):
    
    name = TextInput(label='Playlist Title', placeholder='Title', required=False, min_length=2, max_length=20)
    password = TextInput(label='Playlist Password Leave Empty to Keep it Free', placeholder='Password', required=False, min_length=8)
    url = TextInput(label='External Url', placeholder='https://', required=False, min_length=29)

    def __init__(self):
        self.__stopped = asyncio.get_running_loop().create_future()

    def __stop(self):
        if not self.__stopped.done():
            self.__stopped.set_result(True)

    async def wait(self):
        return await self.__stopped

    async def on_submit(self, interaction: discord.Interaction):
        if self.name is None and self.url is None:
            raise SyntaxError()

        await interaction.response.defer()

        info = {}
        if self.url.value:
            if 'youtu' not in self.url.value and 'playlist' not in self.url.value:
                await interaction.followup.send('This link is not supported.')
                return
            # TODO: Spotify
            info = yt.from_link(str(self.url))
            self.name = self.name or info['title']

        if Playlist.existing(interaction, str(self.name)):
            await interaction.followup.send('This playlist already exists!', ephemeral=True)
            return
            
        playlist = Playlist.new(str(self.name), interaction, password=str(self.password))
        playlist.upload()
        await interaction.followup.send(f'Playlist `{playlist.name}#{playlist.id}` created.')

        playlist.from_youtube(info)
        self.__stop()
    
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        if not isinstance(error, SyntaxError):
            return await super().on_error(interaction, error)
        
        print('Ma sei ghei')

        

class Playlists(slash.Group):

    @slash.command(name='new', description='Creates a playlist.')
    async def new_playlist(self, interaction: discord.Interaction) -> None:
        modal = MNewPlaylist()
        await interaction.response.send_modal(modal)
        
        await modal.wait()

        global cached_playlists
        cached_playlists.append(CachedPlaylist(
            str(modal.name),
            interaction.guild.id if interaction.guild is not None else interaction.user.id,
            interaction.user.id
            ))


    @slash.command(name='show', description='Shows a playlist. If the playlist is private it will be sent as a private message.')
    @slash.describe(name='The name of the playlist.')
    @slash.autocomplete(name=autocomplete)
    async def show_playlist(self, interaction: discord.Interaction, name: str) -> None:
        await interaction.response.defer()

        if not Playlist.existing(interaction, name):
            await interaction.response.send_message(f'`{name}` does not exist.', ephemeral=True)
            return

        playlist = await Playlist.from_database(interaction, name) 

        pView = ui.PlaylistPaginator(playlist)

        if playlist.private:
            await interaction.followup.send('The playlist has been sent you in DMs.')
            await interaction.user.send(embed=playlist.embeds[0], view=pView)
            return

        await interaction.followup.send(embed=playlist.embeds[0], view=pView) 

    @slash.command(name='by', description='Sends an embed with all of your playlists (even if private).')
    async def show_all_playlists(self, interaction: discord.Interaction, person: discord.User | None = None) -> None:
        await interaction.response.defer()

        if person is None:
            person = interaction.user # type: ignore

        assert person is not None

        playlists = await Playlist.from_person(person)
        embed = discord.Embed(
            title=f"{person.display_name}'s Playlists",
            description='Page 1'
        )
        for playlist in playlists:
            embed.add_field(name=playlist.title, value=playlist.date, inline=True)

        await interaction.followup.send(embed=embed)

    @slash.command(name='advices', description='Shows your adviced songs.')
    async def show_advices(self, interaction: discord.Interaction):
        advices = Advices.from_database(interaction.user)
        await interaction.response.send_message(embed=advices.embeds[0], view=ui.MenuView(advices.embeds))