from discord import app_commands as slash

import discord

from models import Advices, LikedSongs, choose as choice, search, Purpose
from models import Players
from models import PlayableSong
from models.utils.errors import SearchingException

from ui import VAdviceableSong


__all__ = (
    'Songs',
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


    @discord.ui.button(emoji='▶️')
    async def play_song(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        await interaction.response.edit_message(view=self)
        
        player = await self.players.load(interaction)
        await interaction.followup.send('Added to Queue.', embed=self.song.embeds[0])
        await player.add_song(self.song, requester=interaction.user)


    @discord.ui.button(emoji='💟')
    async def like_song(self, interaction: discord.Interaction, _):
        playlist = LikedSongs.from_database(interaction.user)
        playlist.add_song(self.song)
        await interaction.response.send_message(f'`{self.song.title} • {self.song.author}` added to `Liked Songs`', ephemeral=True)


    @discord.ui.button(emoji='✒️')
    async def show_lyrics(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.lyrics = not self.lyrics
        if self.lyrics:
            button.style = discord.ButtonStyle.blurple
        else:
            button.style = discord.ButtonStyle.grey
        await interaction.response.edit_message(embed=self.song.embeds[int(self.lyrics)], view=self)


class Songs(slash.Group):

    async def send_error_message(self, interaction: discord.Interaction, cause: str, ephemeral: bool) -> None:
        _embed = discord.Embed(
            title='Something went wrong',
            description=cause,
            color=discord.Color.dark_red()
        )
        if interaction.response.is_done():
            await interaction.followup.send(embed=_embed, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(embed=_embed, ephemeral=ephemeral)
    
    @slash.command(name='advice', description='Advices a song to someone in this server')
    async def advice_song(self, interaction: discord.Interaction, song: str, to: discord.Member) -> None:
        await interaction.response.defer()
        advices = Advices.from_database(to)
        if not song.startswith('http'):
            _song = await choice(interaction, Purpose.Advice, song)
        else:
            _song = search(Purpose.Advice, song)

        embed = _song.embed # type: ignore
        view = VAdviceableSong(_song) # type: ignore

        if _song not in advices.songs:
            advices.add_song(_song) # type: ignore
            message = f"Adviced to {to.mention}"
            
        else:
            message = f"This song is already in {to.display_name}'s advice list"

        await interaction.followup.send(message, embed=embed, view=view)

    @slash.command(name='search', description='Searches a song.')
    async def search_song(self, interaction: discord.Interaction, song: str, choose: bool = True) -> None:
        await interaction.response.defer()
        _song: PlayableSong
        try:
            if choose:
                _song = await choice(interaction, Purpose.Play, song) # type: ignore
            else:
                _song = search(Purpose.Play, song) # type: ignore
        except SearchingException as e:
            await self.send_error_message(interaction, e, ephemeral=True) # type: ignore
            return

        menu = SongMenu(interaction.guild, _song, False)
        await interaction.followup.send(embed=_song.embeds[0], view=menu)

    @slash.command(name='lyrics', description='Shows the lyrics of a song')
    async def search_lyrics(self, interaction: discord.Interaction, song: str, choose: bool = False) -> None:
        await interaction.response.defer()
        _song: PlayableSong
        try:
            if choose:
                _song = await choice(interaction, Purpose.Lyrics, song) # type: ignore
            else:
                _song = search(Purpose.Play, song) # type: ignore
        except SearchingException as e:
            await self.send_error_message(interaction, e, ephemeral=True) # type: ignore
            return

        menu = SongMenu(interaction.guild, _song, True)
        await interaction.response.send_message(embed=_song.embeds[1], view=menu)
