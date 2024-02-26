import discord

import api.queries as queries
from api.local import PlaylistOwnersAPI, PlaylistsAPI
from models import Playlist, Song
from resources import Paginator, PermissionLevel, Privacy

from .generic import MenuView, ResponseView
from .modals import *

__all__ = ("PlaylistPaginator", "PlaylistSettings", "ReminderOptions", "Selector")


class PlaylistPaginator(MenuView):

    def __init__(self, paginator: Paginator, playlist: Playlist) -> None:
        super().__init__(paginator)
        self.playlist = playlist

        self.remove_song.disabled = len(paginator.elements) == 0

    async def has_permission(
        self, user_id: int, permission_lvl: PermissionLevel
    ) -> bool:
        return (
            await PlaylistOwnersAPI.get_owner_level(self.playlist.id, user_id)
            >= permission_lvl
        )

    async def update(self, interaction: discord.Interaction) -> None:
        self.remove_song.disabled = len(self.paginator.elements) == 0
        await self.edit_or_respond(interaction, view=self)

    @discord.ui.button(emoji="➕", style=discord.ButtonStyle.blurple, row=2)
    async def add_song(self, interaction: discord.Interaction, _) -> None:
        if not await self.has_permission(
            interaction.user.id, PermissionLevel.CanAddSongs
        ):
            await interaction.response.send_message(
                "This action required `Add`-level permission to be completed.",
                ephemeral=True,
            )
            return

        modal = AddSong(self.playlist)
        await interaction.response.send_modal(modal)
        await modal.wait()
        await self.update(interaction)

    @discord.ui.button(emoji="➖", style=discord.ButtonStyle.blurple, row=2)
    async def remove_song(self, interaction: discord.Interaction, _) -> None:
        if not await self.has_permission(
            interaction.user.id, PermissionLevel.CanRemoveSongs
        ):
            await interaction.response.send_message(
                "This action required `Remove`-level permission to be completed.",
                ephemeral=True,
            )
            return

        modal = RemoveSong(self.paginator, self.index, self.playlist)
        await interaction.response.send_modal(modal)
        await modal.wait()
        await self.update(interaction)

    @discord.ui.button(emoji="⚙️", style=discord.ButtonStyle.blurple, row=2)
    async def manage_playlist(self, interaction: discord.Interaction, _) -> None:
        if not await self.has_permission(interaction.user.id, PermissionLevel.Admin):
            await interaction.response.send_message(
                "This action requires `Admin`-level permission to be completed.",
                ephemeral=True,
            )
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

    def __init__(self, playlist: Playlist) -> None:
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
        view = PrivacyUpdater(self.playlist)
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
            await interaction.message.delete()  # type: ignore
        self.stop()


class PrivacyUpdater(Settings):

    level: int

    @discord.ui.select(
        placeholder="Select playlist's general permission level",
        options=[
            discord.SelectOption(label=level.name, value=str(level.value))
            for level in Privacy
        ],
    )
    async def set_permission(self, interaction: discord.Interaction, _) -> None:
        await interaction.response.defer()
        self.level = int(interaction.data["values"][0])  # type: ignore[valid-type]
        privacy = Privacy(self.level)
        await PlaylistsAPI.update_privacy(self.playlist.id, privacy)
        await interaction.followup.send(
            f"Playlist's general permission level set to `{privacy.name}`"
        )
        self.stop()


class ReminderOptions(discord.ui.View):

    def __init__(self, user: discord.User, song: Song) -> None:
        super().__init__()
        self.user = user
        self.song = song

    @discord.ui.button(label="Disable")
    async def disable_reminders(self, interaction: discord.Interaction, _) -> None:
        embed = discord.Embed(
            title="Are you sure?",
            description="You can also lower the number of notifications by choosing one day of the week in which to recieve these reminders!",
            colour=discord.Colour.red(),
        ).set_footer(
            text="You can reenable the reminder at anytime by running `/reminders enable`"
        )
        view = Confirmation()
        await interaction.response.send_message(embed=embed, view=view)
        await view.wait()
        if view.response:
            queries.write(
                "UPDATE reminders SET active = 0 WHERE person_id = ?;",
                (interaction.user.id,),
            )
            await interaction.followup.send(
                "Action completed! You won't recieve reminders anymore."
            )
        else:
            await interaction.followup.send("Action cancelled.")

        await interaction.followup.delete()

    @discord.ui.button(label="Already listened?", style=discord.ButtonStyle.red)
    async def remove_song(self, interaction: discord.Interaction, _) -> None:
        playlist_id = queries.read(
            "SELECT rowid FROM playlists WHERE playlist_title = 'Advices' AND playlist_target = ?;",
            (self.user.id,),
        )[0]
        queries.write(
            "REMOVE FROM playlist_songs WHERE song_id = ? AND playlist_id = ?;",
            (self.song.id, playlist_id),
        )

        await interaction.response.send_message("Song removed from your advice list!")


class Confirmation(discord.ui.View):

    response: bool = False

    @discord.ui.button(label="Yes")
    async def confirm(self, interaction: discord.Interaction, _) -> None:
        self.response = True

    @discord.ui.button(label="No")
    async def cancel(self, interaction: discord.Interaction, _) -> None:
        self.response = False


class Selector(MenuView):

    def __init__(self, songs: list[Song]) -> None:
        embeds = [song.embed for song in songs]
        super().__init__(embeds)
        self.songs = songs
        self._current = embeds[0]

    @discord.ui.button(label="✓", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, _) -> None:
        await interaction.response.defer()
        self.song = self.songs[self.index]
        try:
            await interaction.message.delete()  # type: ignore
        except discord.NotFound:
            print("message not found, skipping")
        self.stop()

