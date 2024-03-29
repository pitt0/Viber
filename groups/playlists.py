from discord import app_commands as slash
from discord.ui import TextInput

import discord

import ui
import models.utils.youtube as yt
from models import Playlist, Advices, LikedSongs
from models import UserPlaylist, CachedPlaylist

# init cache
cached_playlists = CachedPlaylist.load()


async def autocomplete(interaction: discord.Interaction, current: str) -> list[slash.Choice[str]]:
    obj = [
        slash.Choice(name=playlist.name, value=playlist.name)
        for playlist in cached_playlists
        if (playlist.showable(interaction) and playlist.is_input(current))
    ]
    return obj



class MNewPlaylist(discord.ui.Modal, title="Create a Playlist"):
    
    name = TextInput(label="Playlist Title", placeholder="Title", required=False, min_length=2, max_length=20)
    password = TextInput(label="Playlist Password Leave Empty to Keep it Free", placeholder="Password", required=False, min_length=8)
    url = TextInput(label="External Url", placeholder="https://", required=False, min_length=29)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.name is None and self.url is None:
            modal = self
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.stop()
            return

        await interaction.response.defer()

        info = {}
        if self.url.value:
            if "youtu" not in self.url.value and "playlist" not in self.url.value:
                await interaction.followup.send("This link is not supported.")
                return
            # TODO: Spotify
            info = yt.from_link(str(self.url))
            self.name = self.name or info["title"]

        if Playlist.existing(interaction, str(self.name)):
            await interaction.followup.send("This playlist already exists!", ephemeral=True)
            return
            
        playlist = Playlist.new(str(self.name), interaction, password=str(self.password))
        playlist.upload()
        await interaction.followup.send(f"Playlist `{playlist.name}#{playlist.id}` created.")

        playlist.from_youtube(info)
        self.stop()



class Playlists(slash.Group):

    @slash.command(name="new", description="Creates a playlist.")
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


    @slash.command(name="show", description="Shows a playlist. If the playlist is private it will be sent as a private message.")
    @slash.describe(name="The name of the playlist.")
    @slash.autocomplete(name=autocomplete)
    async def show_playlist(self, interaction: discord.Interaction, name: str) -> None:
        await interaction.response.defer()

        if not Playlist.existing(interaction, name):
            await interaction.followup.send(f"`{name}` does not exist.", ephemeral=True)
            return

        playlist = await Playlist.from_database(interaction, name) 

        pView = ui.PlaylistPaginator(playlist)

        if playlist.private:
            await interaction.followup.send("The playlist has been sent you in DMs.")
            await interaction.user.send(embed=playlist.embeds[0], view=pView)
            return

        await interaction.followup.send(embed=playlist.embeds[0], view=pView) 

    @slash.command(name="by", description="Sends an embed with all of your playlists (even if private).")
    async def show_all_playlists(self, interaction: discord.Interaction, person: discord.User | None = None) -> None:
        await interaction.response.defer()

        author = person or interaction.user
        embeds = UserPlaylist.embeds(author)

        await interaction.followup.send(embed=embeds[0], view=ui.MenuView(embeds))

    @slash.command(name="advices", description="Shows your adviced songs.")
    async def show_advices(self, interaction: discord.Interaction) -> None:
        advices = Advices.from_database(interaction.user)
        # TODO: Add a settings `⚙️` button before or after the MenuButtons to remove songs
        await interaction.response.send_message(embed=advices.embeds[0], view=ui.MenuView(advices.embeds))

    @slash.command(name="liked", description="Shows your liked songs.")
    async def show_liked_songs(self, interaction: discord.Interaction) -> None:
        liked_songs = LikedSongs.from_database(interaction.user)
        await interaction.response.send_message(embed=liked_songs.embeds[0], view=ui.MenuView(liked_songs.embeds))