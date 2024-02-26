import discord
from discord import ui

from api.local import PlaylistsAPI


class PlaylistCreationModal(ui.Modal, title="Create a Playlist"):

    name = ui.TextInput(
        label="Playlist Title",
        placeholder="Title",
        required=True,
        min_length=2,
        max_length=20,
    )
    # url = TextInput(label="External Url", placeholder="http://", required=False, min_length=29)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if await PlaylistsAPI.exists(self.name, interaction.guild.id):  # type: ignore
            await interaction.response.send_message(
                "A playlist with this name already exists!", ephemeral=True
            )
            return

        await PlaylistsAPI.new(self.name, interaction.guild.id, interaction.user.id)  # type: ignore
        await interaction.response.send_message(f"Playlist `{self.name}` created!")
        self.stop()

    # async def on_submit(self, interaction: discord.Interaction) -> None:
    #     if self.name is None and self.url is None:
    #         modal = self
    #         await interaction.response.send_modal(modal)
    #         await modal.wait()
    #         self.stop()
    #         return

    #     await interaction.response.defer()

    #     if self.url.value:
    #         if (url := yarl.URL(self.url.value)).host is None:
    #             await interaction.followup.send("This url is not supported.")
    #             return

    #         if 'yout' in url.host: # type: ignore
    #             playlist = YouTubePlaylist.get(interaction, str(url))
    #         elif 'spotify' in url.host: # type: ignore
    #             playlist = SpotifyPlaylist.get(interaction, str(url))
    #         else:
    #             await interaction.followup.send("This url is not supported.")
    #             return
    #     else:
    #         if LocalPlaylist.exists(interaction, str(self.name)):
    #             await interaction.followup.send("This playlist already exists!", ephemeral=True)
    #             return
    #         playlist = PlaylistsAPI.create(str(self.name), interaction, PermissionLevel.Viewable)

    #     await playlist.dump(interaction)
    #     await interaction.followup.send(f"Playlist `{playlist.title}` created.")

    #     self.stop()

