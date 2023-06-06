import discord

from .generic import MenuView, ResponseView
from .modals import *
from models import LocalPlaylist
from models import PermissionLevel


__all__ = (
    "PlaylistPaginator",
    "PlaylistSettings"
)


class PlaylistPaginator(MenuView):

    def __init__(self, playlist: LocalPlaylist) -> None:
        super().__init__(playlist.embeds())
        self.playlist = playlist
        if len(self.playlist) == 0:
            self.remove_song.disabled = True

    async def has_permission(self, interaction: discord.Interaction, permission_lvl: int) -> bool:
        if self.playlist.privacy.value < permission_lvl:
            if not await self.playlist.is_owner(interaction.user): # type: ignore
                return False
            if (await self.playlist.owner_level(interaction.user)).value < permission_lvl: # type: ignore
                return False
        return True
    
    async def update(self, interaction: discord.Interaction) -> None:
        self.remove_song.disabled = len(self.playlist) == 0

        self.embeds = self.playlist.embeds()

        await self.edit_or_respond(interaction, view=self)

    @discord.ui.button(emoji='➕', style=discord.ButtonStyle.blurple, row=2)
    async def add_song(self, interaction: discord.Interaction, _) -> None:
        if not await self.has_permission(interaction, 2):
            await interaction.response.send_message('This action required `Add`-level permission to be completed.', ephemeral=True)
            return

        modal = AddSong(self.playlist)
        await interaction.response.send_modal(modal)
        await modal.wait()
        await self.update(interaction)

    @discord.ui.button(emoji='➖', style=discord.ButtonStyle.blurple, row=2)
    async def remove_song(self, interaction: discord.Interaction, _) -> None:
        if not await self.has_permission(interaction, 3):
            await interaction.response.send_message('This action required `Remove`-level permission to be completed.', ephemeral=True)
            return
        
        modal = RemoveSong(self.playlist)
        await interaction.response.send_modal(modal)
        await modal.wait()
        await self.update(interaction)

    @discord.ui.button(emoji="⚙️", style=discord.ButtonStyle.blurple, row=2)
    async def manage_playlist(self, interaction: discord.Interaction, _) -> None:
        if not await self.has_permission(interaction, 4):
            await interaction.response.send_message('This action requires `Admin`-level permission to be completed.', ephemeral=True)
            return
        
        view = PlaylistSettings(self.playlist)
        await self.edit_or_respond(interaction, view=view)
        await view.wait()
        if view.delete:
            return
        
        try:
            await self.update(interaction)
        except discord.HTTPException:
            pass



class Settings(discord.ui.View):

    def __init__(self, playlist: LocalPlaylist) -> None:
        super().__init__()
        self.playlist = playlist

    async def on_timeout(self) -> None:
        self.interaction_check
        return await super().on_timeout()

    @discord.ui.button(label="<")
    async def back(self, *_) -> None:
        self.stop()


class PlaylistSettings(Settings, ResponseView):

    delete: bool

    @discord.ui.button(emoji="⚙️", custom_id="permissions")
    async def advanced_settings(self, interaction: discord.Interaction, _) -> None:
        view = PermissionChanger(self.playlist)
        await self.edit_or_respond(interaction, view=view)
        await view.wait()
        self.delete = view.level == 0 and interaction.guild is not None
        self.stop()

    @discord.ui.button(emoji="🖋️")
    async def rename_playlist(self, interaction: discord.Interaction, _) -> None:
        modal = RenamePlaylist(self.playlist)
        await interaction.response.send_modal(modal)
        await modal.wait()
        await self.edit_or_respond(interaction)
        self.stop()

    @discord.ui.button(emoji="❌", custom_id="delete")
    async def delete_playlist(self, interaction: discord.Interaction, _) -> None:
        modal = DeletePlaylist(self.playlist)
        await interaction.response.send_modal(modal)
        await modal.wait()
        if modal.result:
            self.delete = True
            await interaction.message.delete() # type: ignore
        self.stop()


class PermissionChanger(Settings):

    level: int
    
    @discord.ui.select(placeholder="Select playlist's general permission level", options=[discord.SelectOption(label=level.name, value=level.value) for level in PermissionLevel]) # type: ignore[valid-type]
    async def set_permission(self, interaction: discord.Interaction, _) -> None:
        await interaction.response.defer()
        self.level = int(interaction.data['values'][0]) # type: ignore[valid-type]
        permission = PermissionLevel(self.level)
        await self.playlist.set_privacy(permission)
        await interaction.followup.send(f"Playlist's general permission level set to `{permission.name}`")
        self.stop()