import discord

from .modals import *
from models import Playlist

__all__ = (
    "PlaylistPaginator",
    "PlaylistSettings",
    "PlaylistAdvancedSettings",
    "SongManager",
)

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
        assert (0 <= value <= len(self.embeds) - 1), f"Value set for index: {value}"

        self.page = self.embeds[value]

        self.children[0].disabled = self.children[1].disabled = not value
        self.children[2].disabled = self.children[3].disabled = value == len(self.embeds) -1

        self.__index = value

    @discord.ui.button(label="<<")
    async def _to_first(self, interaction: discord.Interaction, _):
        self.index = 0

        await interaction.response.edit_message(embed=self.page, view=self)

    @discord.ui.button(label="<")
    async def back(self, interaction: discord.Interaction, _):
        self.index -= 1

        await interaction.response.edit_message(embed=self.page, view=self)

    @discord.ui.button(label=">")
    async def fowrard(self, interaction: discord.Interaction, _):
        self.index += 1

        await interaction.response.edit_message(embed=self.page, view=self)

    @discord.ui.button(label=">>")
    async def _to_last(self, interaction: discord.Interaction, _):
        self.index = len(self.embeds) - 1

        await interaction.response.edit_message(embed=self.page, view=self)

    @discord.ui.button(label="Manage", style=discord.ButtonStyle.blurple)
    async def manage_playlist(self, interaction: discord.Interaction, _):
        view = PlaylistSettings(self.playlist)
        await interaction.response.edit_message(view=view)
        await view.wait()
        try:
            view = PlaylistPaginator(self.playlist)
            await interaction.followup.edit_message(interaction.message.id, view=view) # type: ignore
        except discord.HTTPException:
            pass



class PlaylistSettings(discord.ui.View):

    def __init__(self, playlist: Playlist):
        super().__init__()
        self.playlist = playlist

    @discord.ui.button(label="<")
    async def back(self, *_) -> None:
        self.stop()

    @discord.ui.button(label="Advanced")
    async def advanced(self, interaction: discord.Interaction, _) -> None:
        if interaction.user != self.playlist.author:
            await interaction.response.send_message("You cannot complete this action, only the author of the playlist can.", ephemeral=True)
            self.stop()
            return
        view = PlaylistAdvancedSettings(self.playlist)
        await interaction.response.edit_message(view=view)
        await view.wait()
        self.stop()


    @discord.ui.button(label="Songs")
    async def songs(self, interaction: discord.Interaction, _) -> None:
        if self.playlist.private:
            while True:
                modal = AskPassword(self.playlist)
                await interaction.response.send_modal(modal)
                await modal.wait()
                if modal.result:
                    break
        view = SongManager(self.playlist)
        await interaction.response.edit_message(view=view)
        await view.wait()
        self.stop()

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.red)
    async def delete(self, interaction: discord.Interaction, _) -> None:
        if interaction.user != self.playlist.author:
            await interaction.response.send_message("You cannot complete this action, only the author of the playlist can.", ephemeral=True)
            self.stop()
            return

        modal = DeletePlaylist(self.playlist)
        await interaction.response.send_modal(modal)
        await interaction.message.delete() # type: ignore
        self.stop()
        
class PlaylistAdvancedSettings(discord.ui.View):

    children: list[discord.ui.Button]

    def __init__(self, playlist: Playlist):
        super().__init__()
        self.playlist = playlist

        if self.playlist.private:
            self.children[0].label = "Unlock"
        else:
            self.children[0].label = "Lock"

    @discord.ui.button(label="<")
    async def back(self, *_) -> None:
        self.stop()

    @discord.ui.button() # label will be added in __init__
    async def edit_state(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if button.label == "Lock":
            modal = LockPlaylist(self.playlist)
            await interaction.response.send_modal(modal)
            await modal.wait()
            await interaction.message.delete() # type: ignore
        else:
            modal = UnlockPlaylist(self.playlist)
            await interaction.response.send_modal(modal)
            await modal.wait()
        self.stop()

    @discord.ui.button(label="Rename")
    async def rename(self, interaction: discord.Interaction, _) -> None:
        modal = RenamePlaylist(self.playlist)
        await interaction.response.send_modal(modal)
        await modal.wait()
        message = interaction.message
        embed = message.embeds[0] # type: ignore
        embed.title = modal.result
        await interaction.followup.edit_message(message.id, embed=embed) # type: ignore
        self.stop()

class SongManager(discord.ui.View):

    children: list[discord.ui.Button]

    def __init__(self, playlist: Playlist):
        super().__init__()
        self.playlist = playlist
    
    @discord.ui.button(label="<")
    async def back(self, *_) -> None:
        self.stop()

    @discord.ui.button(label="Add")
    async def add_song(self, interaction: discord.Interaction, _) -> None:
        modal = AddSong(self.playlist)
        await interaction.response.send_modal(modal)
        await modal.wait()

    @discord.ui.button(label="Remove")
    async def remove_song(self, interaction: discord.Interaction, _) -> None:
        modal = RemoveSong(self.playlist)
        await interaction.response.send_modal(modal)
        await modal.wait()