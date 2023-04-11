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
                await interaction.response.send_message('You cannot complete this action as this playlist is view-only to non owners.', ephemeral=True)
                return False
            if not (await self.playlist.owner_level(interaction.user)).value < permission_lvl: # type: ignore
                await interaction.response.send_message("You cannot complete this action as you don't have the right permissions.", ephemeral=True)
                return False
        return True
    
    async def update(self, interaction: discord.Interaction) -> None:
        if len(self.playlist) == 0:
            self.remove_song.disabled = True
        else:
            self.remove_song.disabled = False

        await self.edit_or_respond(interaction, view=self)

    @discord.ui.button(emoji='➕', style=discord.ButtonStyle.blurple, row=2)
    async def add_song(self, interaction: discord.Interaction, _) -> None:
        if not await self.has_permission(interaction, 2):
            return

        modal = AddSong(self.playlist)
        await interaction.response.send_modal(modal)
        await modal.wait()
        await self.update(interaction)

    @discord.ui.button(emoji='➖', style=discord.ButtonStyle.blurple, row=2)
    async def remove_song(self, interaction: discord.Interaction, _) -> None:
        if not await self.has_permission(interaction, 3):
            return
        
        modal = RemoveSong(self.playlist)
        await interaction.response.send_modal(modal)
        await modal.wait()
        await self.update(interaction)

    @discord.ui.button(emoji="⚙️", style=discord.ButtonStyle.blurple, row=2)
    async def manage_playlist(self, interaction: discord.Interaction, _) -> None:
        if not await self.has_permission(interaction, 4):
            return
        
        view = PlaylistSettings(self.playlist)
        await self.edit_or_respond(interaction, view=view)
        await view.wait()
        try:
            # view = PlaylistPaginator(self.playlist)
            # await interaction.followup.edit_message(interaction.message.id, view=view) # type: ignore
            # TODO if this does not work try self.stop()
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

    @discord.ui.button(emoji="⚙️", custom_id="permissions")
    async def advanced(self, interaction: discord.Interaction, _) -> None:
        view = PermissionChanger(self.playlist)
        await self.edit_or_respond(interaction, view=view)
        await view.wait()
        ...

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

    @discord.ui.button(emoji="❌", custom_id="delete") # style = discord.ButtonStyle.red
    async def delete(self, interaction: discord.Interaction, _) -> None:
        modal = DeletePlaylist(self.playlist)
        await interaction.response.send_modal(modal)
        await interaction.message.delete() # type: ignore
        self.stop()


class PermissionChanger(Settings):
    
    @discord.ui.select(options=[discord.SelectOption(label=level.name) for level in PermissionLevel])
    async def set_permission(self, interaction: discord.Interaction, select: discord.ui.Select) -> None:
        await interaction.response.defer()
        print(interaction.data)
        print(dir(select))