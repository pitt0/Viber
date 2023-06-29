import discord
from discord.ui import TextInput
from models import LocalPlaylist, SpotifySong
from models import SongsChoice
from resources import SearchingException
from typing import Self




__all__ = (
    "DeletePlaylist",
    "RenamePlaylist",
    "AddSong",
    "RemoveSong"
)


class AddSong(discord.ui.Modal):

    children: list[TextInput[Self]]

    def __init__(self, playlist: LocalPlaylist) -> None:
        super().__init__(title="Add a song")
        self.playlist = playlist

        self.add_item(TextInput(label="Song"))

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"Wait for the bot to search {self.children[0].value}", ephemeral=True)
        try:
            choice = SongsChoice.search(self.children[0].value, SpotifySong)
            song = await choice.choose(interaction)
        except SearchingException as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="There's been an error",
                    description=e,
                    color=discord.Color.dark_red(),
                ),
                ephemeral=True
            )
            return
        if song is None:
            await interaction.response.send_message("Couldn't find anything.", ephemeral=True)
            return

        await self.playlist.add_song(song, interaction.user.id)
        await interaction.followup.send(f"`{song}` has been added to `{self.playlist.title}`!")


class RemoveSong(discord.ui.Modal):

    children: list[TextInput[Self]]

    def __init__(self, playlist: LocalPlaylist) -> None:
        super().__init__(title="Remove a song")
        self.playlist = playlist


        # TODO Another way?
        self.add_item(
            TextInput(
                label="Song index",
                placeholder=f"1 ~ {len(playlist)}"
            )
        )
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        try:
            index = int(self.children[0].value)
        except ValueError:
            await interaction.response.send_message('You must insert a number.', ephemeral=True)
            return
        try:
            song = self.playlist[index-1]
        except IndexError:
            await interaction.response.send_message(f'You have to insert a number between 1 and {len(self.playlist)}', ephemeral=True)
            return
        self.playlist.remove_song(song)
        await interaction.followup.send(f"`{song}` has been removed from `{self.playlist.title}`.", ephemeral=True)
        self.stop()


class DeletePlaylist(discord.ui.Modal):

    children: list[TextInput[Self]]
    result: bool

    def __init__(self, playlist: LocalPlaylist) -> None:
        super().__init__(title="Insert Title to Complete")
        self.playlist = playlist
        name = TextInput(
            label="Title",
            placeholder=playlist.title,
            min_length=len(playlist.title),
            max_length=len(playlist.title)
        )
        self.add_item(name)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.children[0].value != self.playlist.title:
            await interaction.response.send_message("Action cancelled.", ephemeral=True)
            self.result = False
        else:
            await self.playlist.delete()
            await interaction.response.send_message(f"Action completed! `{self.playlist.title}` has been deleted.")
            self.result = True
        self.stop()


class RenamePlaylist(discord.ui.Modal):

    children: list[TextInput[Self]]
    result: str

    def __init__(self, playlist: LocalPlaylist) -> None:
        super().__init__(title="Rename the playlist")
        self.playlist = playlist
        self.add_item(TextInput(label="New Name", default=playlist.title))

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.result = self.children[0].value
        await self.playlist.rename(self.result)
        await interaction.response.send_message(f"Action completed! You renamed the playlist to `{self.playlist.title}`.", ephemeral=True)
        self.stop()