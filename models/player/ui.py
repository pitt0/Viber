from typing import TYPE_CHECKING

import discord

from .queue import Queue
from models.playlists import LikedSongs
from models.songs import LyricsSong


if TYPE_CHECKING:
    from .player import MusicPlayer


class PlayerUI(discord.ui.View):

    children: list[discord.ui.Button]
    message: discord.Message

    def __init__(self, player: "MusicPlayer"):
        super().__init__(timeout=None)
        self.__player = player
        self.message = None # type: ignore

    def destroy(self) -> None:
        self.message = None # type: ignore

    @property
    def queue(self) -> Queue:
        return self.__player.queue

    @property
    def song(self) -> LyricsSong:
        return self.queue.current[0]

    @discord.ui.button(emoji="⏪", disabled=True)
    async def previous(self, interaction: discord.Interaction, _) -> None:
        self.__player.go_back()
        await self.__player.stop(force=False)
        await interaction.response.send_message(f"Song replayed.", ephemeral=True)

    @discord.ui.button(emoji="⏸️")
    async def play_pause(self, interaction: discord.Interaction, _) -> None:
        if self.__player.playing:
            await self.__player.pause()
            await interaction.response.send_message(f"Song paused.", ephemeral=True)
        else:
            await self.__player.resume()
            await interaction.response.send_message(f"Song resumed.", ephemeral=True)

    @discord.ui.button(emoji="⏩", disabled=True)
    async def next(self, interaction: discord.Interaction, _) -> None:
        await self.__player.stop(force=False)
        await interaction.response.send_message(f"Song skipped.", ephemeral=True)

    @discord.ui.button(emoji="💟")
    async def like(self, interaction: discord.Interaction, _) -> None:
        ls = LikedSongs(interaction.user)
        ls.add_song(self.song)
        await interaction.response.send_message(f"Playlist Updated!", ephemeral=True)

    @discord.ui.button(emoji="⏹️", row=1)
    async def stop(self, interaction: discord.Interaction, _) -> None:
        await self.__player.stop()
        await interaction.response.send_message(f"Player stopped.", ephemeral=True)

    @discord.ui.button(emoji="🔀", row=1, disabled=True)
    async def shuffle(self, interaction: discord.Interaction, _) -> None:
        self.queue.shuffle()
        await interaction.response.send_message(f"Queue shuffled.", ephemeral=True)

    @discord.ui.button(emoji="🔁", row=1)
    async def loop(self, interaction: discord.Interaction, _) -> None:
        await self.__player.set_loop(interaction, self.queue.loop + 1 if self.queue.loop != 2 else 0)

    @discord.ui.button(emoji="✒️", row=1)
    async def lyrics(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        message = "\u200b"
        match button.style:
            case discord.ButtonStyle.blurple:
                button.style = discord.ButtonStyle.grey
                message = "Switched to player"
            case discord.ButtonStyle.grey:
                button.style = discord.ButtonStyle.blurple
                message = "Switched to lyrics"
        await self.message.edit(embed=self.song.switch(), view=self)
        await interaction.response.send_message(message, ephemeral=True)