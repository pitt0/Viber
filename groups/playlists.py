from discord import app_commands as slash
from discord.ui import TextInput

import discord
import yarl

import ui
from models import LocalPlaylist, YouTubePlaylist, SpotifyPlaylist, PlaylistPermission
from models import UserLister, CachedPlaylist



async def autocomplete(interaction: discord.Interaction, current: str) -> list[slash.Choice[int]]:
    print('running')
    obj = [
        slash.Choice(name=playlist[1], value=playlist[0])
        for playlist in CachedPlaylist.load(interaction, current)
    ]
    return obj



class MNewPlaylist(discord.ui.Modal, title="Create a Playlist"):
    
    name = TextInput(label="Playlist Title", placeholder="Title", required=False, min_length=2, max_length=20)
    password = TextInput(label="Playlist Password Leave Empty to Keep it Free", placeholder="Password", required=False, min_length=8)
    url = TextInput(label="External Url", placeholder="http://", required=False, min_length=29)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.name is None and self.url is None:
            modal = self
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.stop()
            return

        await interaction.response.defer()

        if (url := yarl.URL(self.url.value)).host is None:
            await interaction.followup.send("This url is not supported.")
            return
        
        if 'yout' in url.host: # type: ignore
            playlist = YouTubePlaylist.get(interaction, str(url))
        elif 'spotify' in url.host: # type: ignore
            playlist = SpotifyPlaylist.get(interaction, str(url))
        else:
            await interaction.followup.send("This url is not supported.")
            return

        if LocalPlaylist.exists(interaction, str(self.name)):
            await interaction.followup.send("This playlist already exists!", ephemeral=True)
            return
            
        playlist = LocalPlaylist.create(str(self.name), interaction, PlaylistPermission.Admin)
        await playlist.dump()
        await interaction.followup.send(f"Playlist `{playlist.title}` created.")

        self.stop()



class Playlists(slash.Group):

    @slash.command(name="new", description="Creates a playlist.")
    async def new_playlist(self, interaction: discord.Interaction) -> None:
        modal = MNewPlaylist()
        await interaction.response.send_modal(modal)
        
        await modal.wait()


    @slash.command(name="show", description="Shows a playlist. If the playlist is private it will be sent as a private message.")
    @slash.describe(name="The name of the playlist.")
    @slash.autocomplete(name=autocomplete)
    async def show_playlist(self, interaction: discord.Interaction, name: int) -> None: # NOTE: name is actually playlist_id
        await interaction.response.defer()

        playlist = await LocalPlaylist.load(interaction, name) 

        pView = ui.PlaylistPaginator(playlist)

        await interaction.followup.send(embed=playlist.embeds()[0], view=pView) 

    @slash.command(name="by", description="Sends an embed with all of your playlists (even if private).")
    async def show_all_playlists(self, interaction: discord.Interaction, person: discord.User | None = None) -> None:
        await interaction.response.defer()

        author = person or interaction.user
        lister = UserLister.load(author, interaction.guild is None and person is None)
        embeds = lister.embeds()

        await interaction.followup.send(embed=embeds[0], view=ui.MenuView(embeds))

    @slash.command(name="advices", description="Shows your adviced songs.")
    async def show_advices(self, interaction: discord.Interaction) -> None:
        advices = await LocalPlaylist.load(interaction, title='Advices', target_id=interaction.user.id)
        # TODO: Add a settings `⚙️` button before or after the MenuButtons to remove songs
        await interaction.response.send_message(embed=advices.embeds()[0], view=ui.MenuView(advices.embeds()))

    @slash.command(name="liked", description="Shows your liked songs.")
    async def show_liked_songs(self, interaction: discord.Interaction) -> None:
        liked_songs = await LocalPlaylist.load(interaction, title='Liked', target_id=interaction.user.id)
        await interaction.response.send_message(embed=liked_songs.embeds()[0], view=ui.MenuView(liked_songs.embeds()))