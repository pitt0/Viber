from typing import TypeAlias
from discord import app_commands as slash
from discord.ext import commands

import discord

from models import Song, MusicPlayer
from models.utils import youtube



GUILD_ID: TypeAlias = int


class Player(slash.Group):

    def __init__(self, client: discord.Client):
        super().__init__()
        self.client = client
        self.players: dict[GUILD_ID, MusicPlayer] = {}


    async def send_me(self, text: str) -> None:
        me = await self.client.fetch_user(648939655579828226)
        await me.send(text)

    def can_connect(self, interaction: discord.Interaction) -> bool:
        assert not isinstance(interaction.user, discord.User)
        return interaction.user.voice is not None and isinstance(interaction.user.voice.channel, discord.VoiceChannel)

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

    async def create_player(self, guild: discord.Guild, voice: discord.VoiceChannel) -> None:
        _player = MusicPlayer(guild)
        self.players[guild.id] = _player
        await _player.connect(voice or _player.voice_client.channel)
        return

    # async def change_presence(self, song: Song) -> None:
    #     activity = discord.Activity(name=song.title, type=discord.ActivityType.listening)
    #     await self.client.change_presence(activity=activity)

    @commands.Cog.listener()
    async def on_error(self, interaction: discord.Interaction, error: slash.CommandInvokeError):
        await self.send_me(f"There's been an error on command {interaction.command.name}.\nError: {error.__class__.__name__}\n          {error}.") # type: ignore
        if isinstance(error, slash.CheckFailure): # TODO: Add a message ig
            return
        _error_embed = discord.Embed(
            title='**Error**',
            description="There's been an error"
        )
        _error_embed.add_field(name=error.__class__.__name__, value=error)
        if interaction.response.is_done():
            await interaction.followup.send(embed=_error_embed)
        else:
            await interaction.response.send_message(embed=_error_embed)


    @commands.Cog.listener('on_voice_state_update')
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        guild: discord.Guild = member.guild
        print(guild.id)
        print(self.players)
        if guild.id not in self.players: 
            return
        _player = self.players[guild.id]
        await _player.voice_update(before, after)
        

    @slash.command(name='connect', description='Connects to a voice channel')
    @slash.check(lambda interaction: interaction.guild is not None)
    @slash.describe(channel='The channel to which you want the bot to connect')
    async def connect(self, interaction: discord.Interaction, channel: discord.VoiceChannel | None = None):
        assert not isinstance(interaction.user, discord.User) and interaction.guild is not None
        _channel: discord.VoiceChannel
        
        if channel is None:
            if not self.can_connect(interaction):
                await self.send_error_message(interaction, cause='Could not connect to a voice channel, try to specify one or connect to one.', ephemeral=True)
                return
            _channel = interaction.user.voice.channel # type: ignore[valid-type]
        else:
            _channel = channel

        await self.create_player(interaction.guild, _channel)


    @slash.command(name='play', description='Plays a song in the server.')
    @slash.check(lambda interaction: isinstance(interaction.channel, discord.TextChannel))
    @slash.describe(reference='A song reference')
    async def play(self, interaction: discord.Interaction, reference: str):
        assert not isinstance(interaction.user, discord.User) and interaction.guild is not None
        channel: discord.VoiceChannel

        await interaction.response.defer()

        if interaction.guild.id not in self.players:
            if not self.can_connect(interaction):
                await self.send_error_message(interaction, cause='Could not connect to a voice channel, try to specify one or connect to one.', ephemeral=True)
                return
            channel = interaction.user.voice.channel # type: ignore[valid-type]
            await self.create_player(interaction.guild, channel)

        title = reference
        if reference.startswith('http'):
            if ('youtube.com' not in reference and 'youtu.be' not in reference):
                await interaction.followup.send('I only accept youtube links.', ephemeral=True)
                return
        else:
            urls = youtube.search_urls(reference)
            if urls is None:
                await interaction.followup.send('Could not find anything.')
                return
            title = urls[0]
        
        song = Song.from_youtube(title)

        await interaction.followup.send('Now playing.', embed=song.embed)
        await self.players[interaction.guild.id].add_song(song)