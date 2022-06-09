import discord

from models import Playlist
from .modals import *


class PlaylistPaginator(discord.ui.View):

    children: list[discord.ui.Button]

    def __init__(self, playlist: Playlist):
        super().__init__()
        self.playlist = playlist
        self.embeds = playlist.embeds

        self.index = 0

    @property
    def index(self) -> int:
        return self.__index

    @index.setter
    def index(self, value: int):
        assert (0 <= value <= len(self.embeds) - 1), f'Value set for index: {value}'

        self.page = self.embeds[value]

        self.children[0].disabled = self.children[1].disabled = not value
        self.children[2].disabled = self.children[3].disabled = value == len(self.embeds) -1

        self.__index = value

    @discord.ui.button(label='<<')
    async def _to_first(self, interaction: discord.Interaction, _):
        self.index = 0

        await interaction.response.edit_message(embed=self.page, view=self)

    @discord.ui.button(label='<')
    async def back(self, interaction: discord.Interaction, _):
        self.index -= 1

        await interaction.response.edit_message(embed=self.page, view=self)

    @discord.ui.button(label='>')
    async def fowrard(self, interaction: discord.Interaction, _):
        self.index += 1

        await interaction.response.edit_message(embed=self.page, view=self)

    @discord.ui.button(label='>>')
    async def _to_last(self, interaction: discord.Interaction, _):
        self.index = len(self.embeds) - 1

        await interaction.response.edit_message(embed=self.page, view=self)

    @discord.ui.button(label='Manage', style=discord.ButtonStyle.blurple)
    async def manage_playlist(self, interaction: discord.Interaction, _):
        view = PlaylistSettings(self.playlist)
        await interaction.response.edit_message(view=view)
        await view.wait()
        await interaction.followup.edit_message(interaction.message.id, view=self) # type: ignore



class PlaylistSettings(discord.ui.View):

    def __init__(self, playlist: Playlist):
        super().__init__()
        self.playlist = playlist

    @discord.ui.button(label='Advanced')
    async def advanced(self, interaction: discord.Interaction, _) -> None:
        if interaction.user != self.playlist.author:
            await interaction.response.send_message('You cannot complete this action, only the author of the playlist can.', ephemeral=True)
            return
        await interaction.response.edit_message(view=PlaylistAdvancedSettings(self.playlist))

    @discord.ui.button(label='Songs')
    async def songs(self, interaction: discord.Interaction, _) -> None:
        if self.playlist.private:
            await interaction.response.send_message(f'You cannot complete this actionneoiahnetiou bEI') # TODO: Ask for password
        await interaction.response.edit_message()

    @discord.ui.button(label='Delete', style=discord.ButtonStyle.red)
    async def delete(self, interaction: discord.Interaction, _) -> None:
        if interaction.user != self.playlist.author:
            await interaction.response.send_message('You cannot complete this action, only the author of the playlist can.', ephemeral=True)
            return

        modal = DeletePlaylist(self.playlist)
        await interaction.response.send_modal(modal)
        await interaction.message.delete() # type: ignore
        
class PlaylistAdvancedSettings(discord.ui.View):

    children: list[discord.ui.Button]

    def __init__(self, playlist: Playlist):
        super().__init__()
        self.playlist = playlist

        if self.playlist.private:
            self.children[0].label = 'Unlock'
        else:
            self.children[0].label = 'Lock'

    @discord.ui.button() # label will be added in __init__
    async def edit_state(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if button.label == 'Lock':
            await interaction.response.send_modal(LockPlaylist(self.playlist))
            await interaction.message.delete() # type: ignore
        else:
            await interaction.response.send_modal(UnlockPlaylist(self.playlist))

    @discord.ui.button(label='Rename')
    async def rename(self, interaction: discord.Interaction, _) -> None:
        await interaction.response.send_modal(RenamePlaylist(self.playlist))

class SongManager(discord.ui.View):

    children: list[discord.ui.Button]

    def __init__(self, playlist: Playlist):
        super().__init__()
        self.playlist = playlist

    @discord.ui.button(label='Add')
    async def add_song(self, interaction: discord.Interaction, _) -> None:
        await interaction.response.send_modal(AddSong(self.playlist))