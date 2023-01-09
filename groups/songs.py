from discord import app_commands as slash
from discord.ext import commands

import discord

from resources import Devs

from models import Advices, LikedSongs, SongsChoice
from models import Players
from models import Song, LyricsSong
from models.utils.errors import SearchingException


__all__ = (
    "Songs",
)


class SongMenu(discord.ui.View):

    def __init__(self, guild: discord.Guild | None, song, lyrics: bool):
        super().__init__()
        self.song = song
        self.players = Players()

        self.play_song.disabled = guild is None

        self.lyrics = lyrics
        if lyrics:
            self.show_lyrics.style = discord.ButtonStyle.blurple


    @discord.ui.button(emoji="▶️")
    async def play_song(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        await interaction.response.edit_message(view=self)
        
        player = await self.players.load(interaction)
        await interaction.followup.send("Added to Queue.", embed=self.song.embeds[0])
        await player.add_song(self.song, requester=interaction.user)


    @discord.ui.button(emoji="💟")
    async def like_song(self, interaction: discord.Interaction, _):
        playlist = LikedSongs.from_database(interaction.user)
        playlist.add_song(self.song)
        await interaction.response.send_message(f"`{self.song.title} • {self.song.author}` added to `Liked Songs`", ephemeral=True)


    @discord.ui.button(emoji="✒️")
    async def show_lyrics(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.lyrics = not self.lyrics
        if self.lyrics:
            button.style = discord.ButtonStyle.blurple
        else:
            button.style = discord.ButtonStyle.grey
        await interaction.response.edit_message(embed=self.song.embeds[int(self.lyrics)], view=self)


class Songs(slash.Group):

    def __init__(self, client: discord.Client):
        super().__init__()
        self.client = client

    # async def send_error_message(self, interaction: discord.Interaction, cause: str, ephemeral: bool) -> None:
    #     _embed = discord.Embed(
    #         title="Something went wrong",
    #         description=cause,
    #         color=discord.Color.dark_red()
    #     )
    #     if interaction.response.is_done():
    #         await interaction.followup.send(embed=_embed, ephemeral=ephemeral)
    #     else:
    #         await interaction.response.send_message(embed=_embed, ephemeral=ephemeral)

    @commands.Cog.listener()
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        # TODO: Check if this works
        # if not try with @error() instead

        dev_message = ""
        usr_message = ""

        match interaction.command:
            case None:
                dev_message = "There's been an unknown error."
                usr_message = "There's been an unknown error, please try again or contact the developer."
            case slash.Command():
                dev_message = f"There's been an error on command _{interaction.command.parent} {interaction.command.name}_"
                usr_message = f"There's been an error trying to run command _{interaction.command.parent} {interaction.command.name}_"
            case slash.ContextMenu():
                dev_message = f"There's been an error on app command _{interaction.command.name}_"
                usr_message = f"There's been an error trying to run app command _{interaction.command.name}_"

        dev_message += (
            f"\n*Error: _{error.__class__.__name__}_*" +
            "\n```" + 
            f"\n{error}" +
            "\n```"
        )

        with Devs() as devs:
            for dev_id in devs:
                dev = await self.client.fetch_user(dev_id)
                await dev.send(dev_message)

        _error_embed = discord.Embed(
            title="**:x: Error**",
            description=usr_message
        ).set_footer(text="Contact the dev at pitto#5732")

        if interaction.response.is_done():
            await interaction.followup.send(embed=_error_embed)
        else:
            await interaction.response.send_message(embed=_error_embed)
    
    @slash.command(name="advice", description="Advices a song to someone in this server")
    async def advice_song(self, interaction: discord.Interaction, song: str, to: discord.Member) -> None:
        await interaction.response.defer()
        advices = Advices.from_database(to)
        if not song.startswith("http"):
            choice = SongsChoice.search(song, Song)
            _song = await choice.choose(interaction)
        else:
            _song = Song.search(song)

        embed = _song.embed

        if _song not in advices.songs:
            advices.add_song(_song)
            message = f"Adviced to {to.mention}"
            
        else:
            message = f"This song is already in {to.display_name}'s advice list"

        await interaction.followup.send(message, embed=embed)

    @slash.command(name="search", description="Searches a song.")
    async def search_song(self, interaction: discord.Interaction, song: str, choose: bool = True) -> None:
        await interaction.response.defer()

        if choose:
            choice = SongsChoice.search(song, LyricsSong)
            _song = await choice.choose(interaction)
        else:
            _song = LyricsSong.search(song)

        menu = SongMenu(interaction.guild, _song, False)
        await interaction.followup.send(embed=_song.embed, view=menu)

    @slash.command(name="lyrics", description="Shows the lyrics of a song")
    async def search_lyrics(self, interaction: discord.Interaction, song: str, choose: bool = False) -> None:
        await interaction.response.defer()
        try:
            if choose:
                choice = SongsChoice.search(song, LyricsSong)
                _song = await choice.choose(interaction)
            else:
                _song = LyricsSong.search(song)
        except SearchingException as e:
            # await self.send_error_message(interaction, e, ephemeral=True)
            return

        menu = SongMenu(interaction.guild, _song, True)
        await interaction.response.send_message(embed=_song.switch(), view=menu) # type: ignore
