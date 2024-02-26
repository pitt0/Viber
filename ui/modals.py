from typing import Self

import discord
from discord.ui import TextInput

from api.local import PlaylistsAPI, PlaylistSongsAPI
from api.local import SongsAPI as SongsAPI
from api.web import SongsAPI as WebSongsAPI
from models import ExternalSong, LocalSong, Playlist
from resources import Paginator, SearchingException, Time

__all__ = ("DeletePlaylist", "RenamePlaylist", "AddSong", "RemoveSong")


class AddSong(discord.ui.Modal):

    children: list[TextInput[Self]]  # type: ignore

    def __init__(self, playlist: Playlist) -> None:
        super().__init__(title="Add a song")
        self.playlist = playlist

        self.add_item(TextInput(label="Song"))

    async def choose_song(
        self, interaction: discord.Interaction, query: str, choices: list[ExternalSong]
    ) -> LocalSong:
        view = Selector(choices)
        await interaction.followup.send(embed=choices[0].embed, view=view)
        await view.wait()
        return await SongsAPI.upload(view.song, query)

    async def _search_song(
        self, interaction: discord.Interaction, query: str, choose: bool
    ) -> LocalSong:
        if query.startswith("http"):
            print(f"[{Time.now()}] Url found, loading.")
            if (song := await WebSongsAPI.load(query)) is None:
                print(f"[{Time.now()}] Url returned nothing, raising Exception.")
                raise ValueError
            print(f"[{Time.now()}] Song found, exiting.")
            return await SongsAPI.upload(song)

        if choose:
            print(f"[{Time.now()}] User set flag choose.")
            if (choices := await WebSongsAPI.search(query)) is None:
                raise ValueError
            print(
                f'[{Time.now()}] Searching "{query}" returned {len(choices)} results.'
            )
            print(f"[{Time.now()}] Letting user choose song.")
            return await self.choose_song(interaction, query, choices)

        else:
            print(f"[{Time.now()}] Skipping choice step.")
            if (song_id := SongCache.load(query)) is not None:
                print(
                    f'[{Time.now()}] "{query}" is present in the cache, loading from database.'
                )
                return await SongsAPI.get_song(song_id)

            else:
                print(
                    f'[{Time.now()}] "{query}" is not present in the database, searching.'
                )
                if (song := await WebSongsAPI.search(query, 1)) is None:
                    raise ValueError
                print(f"[{Time.now()}] Song found, continuing.")
                return await SongsAPI.upload(song[0])

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            f"Wait for the bot to search {self.children[0].value}", ephemeral=True
        )
        try:
            song = await self._search_song(interaction, self.children[0].value, False)
        except SearchingException as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="There's been an error",
                    description=e,
                    colour=discord.Colour.dark_red(),
                ),
                ephemeral=True,
            )
            return

        await PlaylistSongsAPI.add_song(self.playlist.id, song.id, interaction.user.id)
        await interaction.followup.send(
            f"`{song}` has been added to `{self.playlist.title}`!"
        )


class RemoveSong(discord.ui.Modal):

    children: list[TextInput[Self]]

    def __init__(self, paginator: Paginator, page: int, playlist: Playlist) -> None:
        super().__init__(title="Remove a song")
        self.paginator = paginator
        self.playlist = playlist
        self.page = page

        # TODO Another way?
        self.add_item(
            TextInput(label="Song index", placeholder=f"1 ~ 12")  # NOTE: bound to page
        )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        try:
            index = int(self.children[0].value)
        except ValueError:
            await interaction.response.send_message(
                "You must insert a number.", ephemeral=True
            )
            return

        if not 1 <= index <= 12:
            await interaction.response.send_message(
                "You have to insert a number between 1 and 12", ephemeral=True
            )
            return

        song = self.paginator.remove_element(self.page, index)
        await interaction.followup.send(
            f"`{song}` has been removed from `{self.playlist.title}`.", ephemeral=True
        )
        self.stop()


class DeletePlaylist(discord.ui.Modal):

    children: list[TextInput[Self]]
    result: bool

    def __init__(self, playlist: Playlist) -> None:
        super().__init__(title="Insert Title to Complete")
        self.playlist = playlist
        name = TextInput(
            label="Title",
            placeholder=playlist.title,
            min_length=len(playlist.title),
            max_length=len(playlist.title),
        )
        self.add_item(name)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.children[0].value != self.playlist.title:
            await interaction.response.send_message("Action cancelled.", ephemeral=True)
            self.result = False
        else:
            await PlaylistsAPI.delete_playlist(self.playlist.id)
            await interaction.response.send_message(
                f"Action completed! `{self.playlist.title}` has been deleted."
            )
            self.result = True
        self.stop()


class RenamePlaylist(discord.ui.Modal):

    children: list[TextInput[Self]]
    result: str

    def __init__(self, playlist: Playlist) -> None:
        super().__init__(title="Rename the playlist")
        self.playlist = playlist
        self.add_item(TextInput(label="New Name", default=playlist.title))

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.result = self.children[0].value
        await PlaylistsAPI.rename(self.playlist.id, self.result)
        await interaction.response.send_message(
            f"Action completed! You renamed the playlist to `{self.playlist.title}`.",
            ephemeral=True,
        )
        self.stop()

