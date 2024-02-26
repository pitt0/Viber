import discord
from discord import app_commands as slash
from discord.ext import commands

import ui
from api.autocomplete import Cached
from api.local.playlists import *
from resources import Paginator, PermissionLevel

from .searcher import SongSearcher
from .ui import PlaylistCreationModal
from .utils import autocomplete


class Playlists(commands.GroupCog, SongSearcher):

    @slash.command(name="new", description="Creates a playlist.")
    async def new_playlist(self, interaction: discord.Interaction) -> None:
        modal = PlaylistCreationModal()
        await interaction.response.send_modal(modal)

    @slash.command(name="add-song", description="Add a song to a playlist.")
    @slash.autocomplete(
        playlist=autocomplete(Cached.playlists, PermissionLevel.CanAddSongs)
    )
    async def add_song(
        self,
        interaction: discord.Interaction,
        playlist: str,
        song: str,
        choose: bool = True,
    ) -> None:
        # author_owner_level = await PlaylistOwnersAPI.get_owner_level(playlist, interaction.user.id)
        # if author_owner_level < PermissionLevel.CanAddSongs:
        #     await interaction.response.send_message('You do not have enough permissions to complete this action')

        _song = await self._search_song(interaction, song, choose)
        _playlist = await PlaylistsAPI.get_playlist(playlist_id=playlist)

        if await PlaylistSongsAPI.is_present(_playlist.id, _song.id):
            await interaction.response.send_message(
                f"This song is already in `{_playlist.title}`.", ephemeral=True
            )
            return

        await PlaylistSongsAPI.add_song(_playlist.id, _song.id, interaction.user.id)
        await interaction.response.send_message(
            f"`{_song}` added to `{_playlist.title}`"
        )

    @slash.command(name="remove-song", description="Remove a song from a playlist.")
    @slash.autocomplete(
        playlist=autocomplete(Cached.playlists, PermissionLevel.CanRemoveSongs),
        song=autocomplete(Cached.songs),
    )
    @slash.describe(
        songs="Only the songs that are present in the database will be shown."
    )
    async def remove_song(
        self, interaction: discord.Interaction, playlist: str, song: str
    ) -> None:
        await PlaylistSongsAPI.remove_song(playlist, song)
        await interaction.response.send_message("Action completed!")

    @slash.command(name="edit-owner", description="Take action on a playlist owner.")
    @slash.autocomplete(playlist=autocomplete(Cached.playlists, PermissionLevel.Admin))
    async def update_owner(
        self,
        interaction: discord.Interaction,
        playlist: str,
        user: discord.Member,
        permission_level: PermissionLevel,
        ephemeral: bool = False,
    ) -> None:
        await PlaylistOwnersAPI.add_owner(playlist, user.id, permission_level)
        playlist_name = await PlaylistsAPI.get_title(playlist)
        match permission_level:
            case PermissionLevel.Extern:
                message = (
                    f"{user.mention} has been removed from `{playlist_name}`'s owners."
                )
            case PermissionLevel.CanView:
                message = f"{user.mention} will now be able to see `{playlist_name}`, even if it is private."
            case PermissionLevel.CanAddSongs:
                message = f"{user.mention} will now be able to add songs to `{playlist_name}`, even if it's privacy settings wouldn't allow it."
            case PermissionLevel.CanRemoveSongs:
                message = f"{user.mention} will now be able to remove songs to `{playlist_name}`, even if it's privacy settings wouldn't allow it."
            case PermissionLevel.Admin:
                message = f"{user.mention} is now considered an admin of `{playlist_name}` and can complete any action on it."

        await interaction.response.send_message(
            f"Done! {message}!", ephemeral=ephemeral
        )

    # @slash.command(name='ownership', description='Describes how playlists are managed by owners.')
    # async def ownership_info(self, interaction: discord.Interaction) -> None:
    #     # TODO: Check if this turns into 1,2,3,4,5
    #     MESSAGE = (
    #         "There are 5 levels of ownership of a playlist:"
    #         "\n> 0. The user cannot perform any action on the playlist, nor even see the playlist if private."
    #         "\n> 1. The user can see the playlist, but cannot perform any action."
    #         "\n> 2. The user can add songs to the playlist (but cannot remove them)."
    #         "\n> 3. The user can add and remove songs to the playlist."
    #         "\n> 4. The user is considered an admin and can manage songs in the playlist, as well as rename and delete the playlist."
    #     )
    #     await interaction.response.send_message(MESSAGE)

    @slash.command(
        name="show",
        description="Shows a playlist. If the playlist is private it will be sent as a private message.",
    )
    @slash.autocomplete(name=autocomplete(Cached.playlists))
    async def show_playlist(self, interaction: discord.Interaction, name: str) -> None:
        # NOTE: name is actually playlist_id
        playlist = await PlaylistsAPI.get_playlist(playlist_id=name)
        playlist_songs = await PlaylistSongsAPI.get_songs(playlist_id=name)

        paginator = Paginator(
            playlist.title,
            playlist_songs,
            "title",
            "artists",
            discord.Colour.blurple(),
            dynamic=True,
        )
        pView = ui.PlaylistPaginator(paginator, playlist)
        await interaction.followup.send(embed=paginator.get_current(0), view=pView)

    @slash.command(
        name="by", description="Sends an embed with all of a user's playlists."
    )
    @slash.describe(person="If nothing is passed, it defaults to you.")
    async def show_all_playlists(
        self, interaction: discord.Interaction, person: discord.User | None = None
    ) -> None:
        author = person or interaction.user
        lister = await PlaylistsAPI.get_playlists(
            user_id=author.id
        )  # interaction.guild is None and person is None
        paginator = Paginator(
            f"{author.display_name}'s Playlists",
            lister,
            "title",
            "date",
            discord.Colour.orange(),
        )
        await interaction.response.send_message(
            embed=paginator.get_current(0), view=ui.MenuView(paginator)
        )

    @slash.command(name="here", description="Shows all the playlist of this server.")
    @slash.guild_only
    async def show_here(self, interaction: discord.Interaction) -> None:
        lister = await PlaylistsAPI.get_playlists(guild_id=interaction.guild.id)  # type: ignore[non-null]
        paginator = Paginator(f"{interaction.guild.name}'s Playlists", discord.Colour.dark_green(), lister, "title", "date")  # type: ignore[non-null]
        await interaction.followup.send(
            embed=paginator.get_current(0), view=ui.MenuView(paginator)
        )
