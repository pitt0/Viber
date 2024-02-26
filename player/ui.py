from typing import TYPE_CHECKING

import discord

from api.local import FavouritesAPI
from models.songs import Song

from .queue import Queue

if TYPE_CHECKING:
    from .player import MusicPlayer


class PlayerUI(discord.ui.View):

    children: list[discord.ui.Button]  # type: ignore
    message: discord.Message

    def __init__(self, player: "MusicPlayer"):
        super().__init__(timeout=None)
        self.__player = player
        self.message = None  # type: ignore

    async def destroy(self) -> None:
        await self.message.delete()
        self.message = None  # type: ignore

    @property
    def queue(self) -> Queue:
        return self.__player.queue

    @property
    def song(self) -> Song:
        return self.queue.current[0]

    @discord.ui.button(emoji="⏪", disabled=True)
    async def previous(self, interaction: discord.Interaction, _) -> None:
        self.__player.go_back()
        await self.__player.stop(force=False)
        await interaction.response.send_message("Song replayed.", ephemeral=True)

    @discord.ui.button(emoji="⏸️")
    async def play_pause(self, interaction: discord.Interaction, _) -> None:
        if self.__player.playing:
            await self.__player.pause()
            await interaction.response.send_message("Song paused.", ephemeral=True)
        else:
            await self.__player.resume()
            await interaction.response.send_message("Song resumed.", ephemeral=True)

    @discord.ui.button(emoji="⏩", disabled=True)
    async def next(self, interaction: discord.Interaction, _) -> None:
        await self.__player.stop(force=False)
        await interaction.response.send_message("Song skipped.", ephemeral=True)

    @discord.ui.button(emoji="💟")
    async def like(self, interaction: discord.Interaction, _) -> None:
        await FavouritesAPI.add_song(interaction.user.id, self.song.id)
        await interaction.response.send_message("Playlist Updated!", ephemeral=True)

    @discord.ui.button(emoji="⏹️", row=1)
    async def _stop(self, interaction: discord.Interaction, _) -> None:
        await self.__player.stop()
        await interaction.response.send_message("Player stopped.", ephemeral=True)

    @discord.ui.button(emoji="🔀", row=1, disabled=True)
    async def shuffle(self, interaction: discord.Interaction, _) -> None:
        self.queue.shuffle()
        await interaction.response.send_message("Queue shuffled.", ephemeral=True)

    @discord.ui.button(emoji="🔁", row=1)
    async def loop(self, interaction: discord.Interaction, _) -> None:
        await self.__player.set_loop(
            interaction, self.queue.loop + 1 if self.queue.loop != 2 else 0
        )

    @discord.ui.button(emoji="✒️", row=1)
    async def lyrics(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        message = "\u200b"
        match button.style:
            case discord.ButtonStyle.blurple:
                button.style = discord.ButtonStyle.grey
                message = "Switched to player"
            case discord.ButtonStyle.grey:
                button.style = discord.ButtonStyle.blurple
                message = "Switched to lyrics"
        await self.message.edit(embed=self.song.lyrics, view=self)
        await interaction.response.send_message(message, ephemeral=True)

