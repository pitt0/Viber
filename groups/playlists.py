from discord import app_commands as slash
from discord.ui import TextInput

import discord
import resources as res
from resources import Playlist, IDENTIFIER



def create_playlist(name: str, interaction: discord.Interaction, password: str | None = None) -> Playlist:
    return Playlist(name, interaction.user, interaction.guild, password=password, private=password is not None) # type: ignore



class MNewPlaylist(discord.ui.Modal, title='Create a Playlist'):
    
    name = TextInput(label='Playlist Title', placeholder='Title', required=True, min_length=2, max_length=20)
    password = TextInput(label='Playlist Password Leave Empty to Keep it Free', placeholder='Password', required=False, min_length=8)
    # url = TextInput(label='External Url', placeholder='Url', required=False, min_length=25)

    async def callback(self, interaction: discord.Interaction):
        if Playlist.existing(interaction.guild.id, str(self.name)): # type: ignore
            await interaction.response.send_message('This playlist already exists!', ephemeral=True)
            return

        playlist = create_playlist(str(self.name), interaction, str(self.password))
        playlist.upload()
        await interaction.response.send_message(f'Playlist `{playlist.name}#{playlist.id}` created.')



class Playlists(slash.Group):

    def __init__(self, client: discord.Client):
        super().__init__()
        self.client = client

    
    @slash.command(name='new', description='Creates a playlist.')
    async def new_playlist(self, interaction: discord.Interaction) -> None:

        modal = MNewPlaylist()
        await interaction.response.send_modal(modal)


    @slash.command(name='show', description='Shows a playlist. If the playlist is private it will be sent as a private message.')
    @slash.describe(name='The name of the playlist.', id='The id of the playlist you want to edit.')
    async def show_playlist(self, interaction: discord.Interaction, name: str | None = None, id: int | None = None) -> None:
        reference: IDENTIFIER

        if name is None and id is None:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Missing Parameters!", 
                    description=f'You have to include either the name or the id of the playlist!', 
                    color=discord.Color.red()
                    ),
                ephemeral=True
                )
            return

        reference = name or id  # type: ignore

        playlist = Playlist.from_database(interaction.guild.id, reference) # type: ignore

        if playlist is None:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Couldn't find anything :c", 
                    description=f'Searching for `{reference}` into database returned no result.', 
                    color=discord.Color.red()
                    )
                )
            return

        # When fetching from database author and guild are set as their own IDs
        # so here I convert them
        playlist.author = await self.client.fetch_user(playlist.author) # type: ignore
        playlist.guild = await self.client.fetch_guild(playlist.guild) # type: ignore

        

        pEmbed = discord.Embed(
            title=playlist.name,
            description=f"by {playlist.author.display_name}",
            color=discord.Color.blurple()
        )
        pView = res.VPlaylist(playlist)
        for song in playlist.songs:
            pEmbed.add_field(name=song.title, value=f"{song.author} • {song.album}", inline=True)

        if playlist.private:
            await interaction.response.pong()
            await interaction.user.send(embed=pEmbed, view=pView)
            return  

        await interaction.response.send_message(embed=pEmbed, view=pView) 
