import discord
from discord import app_commands as slash
from discord.ext import commands

import ui
from api.autocomplete import Cached
from api.local import FavouritesAPI, SongsAPI
from resources import Paginator

from .searcher import SongSearcher
from .utils import autocomplete


class Favourites(commands.GroupCog, SongSearcher):

    @slash.command(name="show", description="Shows your favourites songs.")
    async def show_songs(self, interaction: discord.Interaction) -> None:
        favourites = await FavouritesAPI.get_favourites(interaction.user.id)
        paginator = Paginator(
            f"{interaction.user.display_name}'s Favourites songs",
            favourites,
            "title",
            "artists",
            discord.Colour.dark_red(),
        )
        await interaction.response.send_message(
            embed=paginator.get_current(0), view=ui.MenuView(paginator)
        )

    @slash.command(name="add", description="Adds a song to your favourites.")
    @slash.describe(choose="Choose between the results of the query.")
    async def add_song(
        self, interaction: discord.Interaction, song: str, choose: bool = False
    ) -> None:
        await interaction.response.defer()
        favourites = await FavouritesAPI.get_favourites(interaction.user.id)
        _song = await self._search_song(interaction, song, choose)

        if _song not in favourites:
            await FavouritesAPI.add_song(interaction.user.id, _song.id)
            message = f"{_song.title} added to your favourites!"
        else:
            message = "This song already is in favourites list."

        await interaction.followup.send(message, embed=_song.embed)

    @slash.command(name="remove", description="Removes a song from your favourites.")
    @slash.autocomplete(song=autocomplete(Cached.favourites))
    async def remove_song(self, interaction: discord.Interaction, song: str) -> None:
        _song = await SongsAPI.get_song(song)
        await FavouritesAPI.remove_song(interaction.user.id, _song.id)
        await interaction.response.send_message(
            f"Done! {_song.title} removed from your favourites!"
        )
