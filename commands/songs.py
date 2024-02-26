import discord
from .utils import FailableCog, Players, search_song
from api.local import SongsAPI as SongsAPI, AdvicesAPI, FavouritesAPI
from discord import app_commands as slash
from discord.ext import commands
from models import Song, ExternalSong, LocalSong
from resources import SearchingException, Time


__all__ = 'Songs',


class Songs(FailableCog):

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot

    @commands.hybrid_command(name="advise", description="Advise a song to someone in this server")
    @slash.describe(choose='Choose between the results of the query.')
    async def advice_song(self, context: commands.Context, query: str, to: discord.Member, choose: bool = False) -> None:
        await context.defer()
        advices = await AdvicesAPI.get_advices(to.id)
        song = await search_song(context, query, choose)

        if song not in advices:
            await AdvicesAPI.add_song(to.id, song.id, context.author.id)
            message = f"Song advised to {to.mention}"
        else:
            message = f"This song is already in {to.display_name}'s advice list"

        await context.send(message, embed=song.embed)

    @commands.hybrid_command(name="search", description="Search a song.")
    @slash.describe(choose='Choose between all the results.')
    async def search_song(self, context: commands.Context, query: str, choose: bool = True) -> None:
        await context.defer()
        print(f'[{Time.now()}] Searching "{query}".')
        song = await search_song(context, query, choose)

        menu = SongMenu(context.guild, song, False)
        await context.send(embed=song.embed, view=menu)
        print(f'[{Time.now()}] SongMenu sent.')

    # @commands.hybrid_command(name="lyrics", description="Shows the lyrics of a song.")
    # @slash.describe(choose='Choose between the results of the query.')
    # async def search_lyrics(self, context: commands.Context, query: str, choose: bool = False) -> None:
    #     await context.defer()
    #     song = await search_song(context, query, choose)

    #     menu = SongMenu(context.guild, song, True)
    #     await context.send(embed=song.lyrics, view=menu)


class SongMenu(discord.ui.View):

    def __init__(self, guild: discord.Guild | None, song: Song, lyrics: bool) -> None:
        super().__init__()
        self.song = song
        self.players = Players()

        self.play_song.disabled = guild is None

        # self.lyrics = lyrics
        # if lyrics:
        #     self.show_lyrics.style = discord.ButtonStyle.blurple

    @discord.ui.button(emoji="▶️")
    async def play_song(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        assert isinstance(interaction.user, discord.Member) and interaction.guild is not None # NOTE: typechecking
        button.disabled = True
        await interaction.response.edit_message(view=self)

        player = await self.players.load(interaction)
        await interaction.followup.send("Added to Queue.", embed=self.song.embed)
        await player.add_song(self.song, requester=interaction.user) # TODO: ?????

    @discord.ui.button(emoji="💟")
    async def like_song(self, interaction: discord.Interaction, _) -> None:
        await FavouritesAPI.add_song(interaction.user.id, self.song.id)
        await interaction.response.send_message(f"`{self.song.title} • {self.song.author}` added to `Liked Songs`", ephemeral=True)

    # @discord.ui.button(emoji="✒️")
    # async def show_lyrics(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
    #     self.lyrics = not self.lyrics
    #     if self.lyrics:
    #         button.style = discord.ButtonStyle.blurple
    #     else:
    #         button.style = discord.ButtonStyle.grey
    #     await interaction.response.edit_message(embed=self.song.embeds[int(self.lyrics)], view=self)
