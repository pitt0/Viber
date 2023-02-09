import discord

from .generic import MenuView
from .modals import *
from models import Playlist


__all__ = (
    "PlaylistPaginator",
    "PlaylistSettings",
    "PlaylistAdvancedSettings",
    "SongManager",
)


class PlaylistPaginator(MenuView):

    def __init__(self, playlist: Playlist):
        super().__init__(playlist.embeds)
        self.playlist = playlist

    @discord.ui.button(emoji="⚙️", style=discord.ButtonStyle.blurple)
    async def manage_playlist(self, interaction: discord.Interaction, _):
        view = PlaylistSettings(self.playlist)
        await self.respond(interaction, view=view)
        await view.wait()
        try:
            view = PlaylistPaginator(self.playlist)
            await interaction.followup.edit_message(interaction.message.id, view=view) # type: ignore
        except discord.HTTPException:
            pass



class Settings(discord.ui.View):

    def __init__(self, playlist: Playlist):
        super().__init__()
        self.playlist = playlist

    async def on_timeout(self) -> None:
        self.interaction_check
        return await super().on_timeout()

    @discord.ui.button(label="<")
    async def back(self, *_) -> None:
        self.stop()


class PlaylistSettings(Settings):

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data["custom_id"] == "songs": # type: ignore
            return True
            
        if interaction.user != self.playlist.author:
            await interaction.response.send_message("You cannot perform this action, only the author of the playlist can.", ephemeral=True)
            return False
        
        return True

    @discord.ui.button(emoji="⚙️", custom_id="advanced")
    async def advanced(self, interaction: discord.Interaction, _) -> None:
        view = PlaylistAdvancedSettings(self.playlist)
        await interaction.response.edit_message(view=view)
        await view.wait()
        self.stop()

    @discord.ui.button(emoji="🎶", custom_id="songs")
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

    @discord.ui.button(emoji="❌", custom_id="delete") # style = discord.ButtonStyle.red
    async def delete(self, interaction: discord.Interaction, _) -> None:
        modal = DeletePlaylist(self.playlist)
        await interaction.response.send_modal(modal)
        await interaction.message.delete() # type: ignore
        self.stop()

        
class PlaylistAdvancedSettings(Settings):

    def __init__(self, playlist: Playlist):
        super().__init__(playlist)

        if self.playlist.private:
            self.edit_state.emoji = "🔓"
        else:
            self.edit_state.emoji = "🔒"

    @discord.ui.button() # emoji will be added in __init__
    async def edit_state(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if button.emoji == "🔒":
            modal = LockPlaylist(self.playlist, interaction.message) # type: ignore
        else:
            modal = UnlockPlaylist(self.playlist)

        await interaction.response.send_modal(modal)
        await modal.wait()
        self.stop()

    @discord.ui.button(emoji="🖋️")
    async def rename(self, interaction: discord.Interaction, _) -> None:
        modal = RenamePlaylist(self.playlist)
        await interaction.response.send_modal(modal)
        await modal.wait()
        message = interaction.message
        embed = message.embeds[0] # type: ignore
        embed.title = modal.result
        await interaction.followup.edit_message(message.id, embed=embed) # type: ignore
        self.stop()


class SongManager(Settings):

    @discord.ui.button(emoji="➕")
    async def add_song(self, interaction: discord.Interaction, _) -> None:
        modal = AddSong(self.playlist)
        await interaction.response.send_modal(modal)
        await modal.wait()

    @discord.ui.button(emoji="➖")
    async def remove_song(self, interaction: discord.Interaction, _) -> None:
        modal = RemoveSong(self.playlist)
        await interaction.response.send_modal(modal)
        await modal.wait()