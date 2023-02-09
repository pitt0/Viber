from discord.ui import TextInput
from typing import Self

import discord

from .generic import WaitableModal
from models import Playlist, Song
from models import SongsChoice
from models.utils.errors import SearchingException



__all__ = (
    "DeletePlaylist",
    "LockPlaylist",
    "UnlockPlaylist",
    "RenamePlaylist",
    "AddSong",
    "AskPassword",
    "RemoveSong"
)



class DeletePlaylist(discord.ui.Modal):

    children: list[TextInput[Self]]

    def __init__(self, playlist: Playlist):
        super().__init__(title="Insert Name to Complete")
        self.playlist = playlist
        name = TextInput(
            label="Title",
            placeholder=playlist.name,
            min_length=len(playlist.name),
            max_length=len(playlist.name)
        )
        self.add_item(name)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.children[0].value != self.playlist.name:
            await interaction.response.send_message("Action cancelled.", ephemeral=True)
        else:
            self.playlist.delete()
            await interaction.response.send_message(f"Action completed! {self.playlist.name} has been deleted.")


class LockPlaylist(WaitableModal):

    children: list[TextInput[Self]]

    def __init__(self, playlist: Playlist, message: discord.Message):
        super().__init__(title="Fill the fields to lock the playlist")
        self.message = message
        self.playlist = playlist
        password = TextInput(
            label="Password",
            min_length=8
        )
        self.add_item(password)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.playlist.set_password(self.children[0].value)
        self.playlist.lock()
        await self.message.delete()
        await interaction.response.send_message(f"Action completed! {self.playlist.name} is now private.")
        self.stop()

class UnlockPlaylist(WaitableModal):

    children: list[TextInput[Self]]

    def __init__(self, playlist: Playlist):
        super().__init__(title="Fill the fields to lock the playlist")
        self.playlist = playlist
        password = TextInput(
            label="Password",
            min_length=8
        )
        self.add_item(password)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.children[0].value != self.playlist.password:
            await interaction.response.send_message(f"Invalid password", ephemeral=True)
            return
        self.playlist.unlock()
        await interaction.response.send_message(f"Action completed! {self.playlist.name} is now free.")

class RenamePlaylist(WaitableModal):

    children: list[TextInput[Self]]

    def __init__(self, playlist: Playlist):
        super().__init__(title="Rename the playlist")
        self.playlist = playlist
        self.add_item(
            TextInput(
                label="New Name"
            )
        )
        if playlist.private:
            self.add_item(
                TextInput(
                    label="Password",
                    min_length=8
                )
            )

        self.result = ""

    async def on_submit(self, interaction: discord.Interaction):
        if len(self.children) == 2 and self.children[1].value != self.playlist.password:
            await interaction.response.send_message(f"Invalid password", ephemeral=True)
            return

        self.result = self.children[0].value
        self.playlist.rename(self.children[0].value)
        await interaction.response.send_message(f"Action completed! You renamed the playlist to {self.playlist.name}.")
        self.stop()

class AddSong(discord.ui.Modal):

    children: list[TextInput[Self]]

    def __init__(self, playlist: Playlist):
        super().__init__(title="Add a song")
        self.playlist = playlist

        self.add_item(
            TextInput(
                label="Song",
                placeholder="http://"
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Wait for the bot to search for `{self.children[0].value}`", ephemeral=True)
        try:
            choice = SongsChoice.search(self.children[0].value, Song)
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

        self.playlist.add_song(song)
        if interaction.response.is_done():
            await interaction.followup.send(f"`{song}` has been added to {self.playlist.name}!")
        else:
            await interaction.response.send_message(f"`{song}` has been added to {self.playlist.name}!")

class RemoveSong(discord.ui.Modal):

    children: list[TextInput[Self]]

    def __init__(self, playlist: Playlist):
        super().__init__(title="Remove a song")
        self.playlist = playlist

        self.add_item(
            TextInput(
                label="Song index",
                placeholder=f"1 ~ {len(playlist)}"
            )
        )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            index = int(self.children[0].value)
        except ValueError:
            await interaction.response.send_message(f"You must insert a number.", ephemeral=True)
            return
        song = self.playlist[index-1]
        self.playlist.remove_song(song)
        await interaction.response.send_message(f"`{song}` has been removed from {self.playlist.name}.")

class AskPassword(WaitableModal):

    children: list[TextInput[Self]]

    def __init__(self, playlist: Playlist):
        super().__init__(title="Insert Password")
        self.playlist = playlist

        self.add_item(
            TextInput(
                label="Insert Password",
                placeholder="Password"
            )
        )

        self.result = 0

    async def on_submit(self, interaction: discord.Interaction):
        if self.children[0].value == self.playlist.password:
            await interaction.response.send_message(f"Accepted! Wait...")
            self.result = 1
        else:
            await interaction.response.send_message(f"Wrong password, please retry.")
            self.result = 0
        self.stop()