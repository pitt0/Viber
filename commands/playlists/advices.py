import random
from pathlib import Path

import discord
from discord import app_commands as slash
from discord.ext import commands

import ui
from api.autocomplete import Cached
from resources import Paginator
from sql import Connection

from .searcher import SongSearcher
from .utils import autocomplete


def read_query(path: str) -> str:
    return Path(path).read_text()


type AdviceSongs = list[tuple[str, str]]


class Advices(commands.GroupCog, SongSearcher):

    @slash.command(name="show", description="Shows your adviced songs.")
    async def show_advices(self, interaction: discord.Interaction) -> None:
        with Connection() as cursor:
            songs: AdviceSongs = cursor.execute(
                read_query("sql/custom/get_advices.sql"), ("user_id=? AND playlist_type='Advices'", interaction.user.id)
            ).fetchall()
        paginator = Paginator(f"{interaction.user}'s Advice list", songs, 0, 1, discord.Colour.red())  # type: ignore
        await interaction.response.send_message(embed=paginator.get_current(0), view=ui.MenuView(paginator))

    @slash.command(name="random", description="Sends a random song from your adviced songs.")
    async def random_advice(self, interaction: discord.Interaction) -> None:
        advices = await AdvicesAPI.get_advices(interaction.user.id)
        # TODO: Add context and maybe change embed
        await interaction.response.send_message(embed=random.choice(advices).embed)

    @slash.command(name="give", description="Advice a song to someone.")
    @slash.describe(
        mention="Whether to mention or not the user when the operation is completed.",
        choose="Choose between the results of the query.",
    )
    async def give_advice(
        self,
        interaction: discord.Interaction,
        song: str,
        to: discord.Member,
        mention: bool = True,
        choose: bool = False,
    ) -> None:
        await interaction.response.defer()
        advices = await AdvicesAPI.get_advices(to.id)
        _song = await self._search_song(interaction, song, choose)

        if _song in advices:
            await interaction.followup.send(
                f"This song is already in {to.display_name}'s advice list",
                embed=_song.embed,
            )
            return

        await AdvicesAPI.add_song(to.id, _song.id, interaction.user.id)
        if mention:
            message = f"Adviced to {to.mention}"
        else:
            message = f"Adviced to {to.display_name}"

        await interaction.followup.send(message, embed=_song.embed)

    @slash.command(name="remove", description="Remove a song from your adviced songs.")
    @slash.autocomplete(song=autocomplete(Cached.advices))
    async def remove_advice(self, interaction: discord.Interaction, song: str) -> None:
        _song = await SongsAPI.get_song(song)
        await AdvicesAPI.remove_song(interaction.user.id, _song.id)
        await interaction.response.send_message(f"Done! {_song.title} removed from your advices!")
