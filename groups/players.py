from typing import Literal, TypeAlias
from discord import app_commands as slash
from discord.ext import commands

import discord

from models import search, choose as choice, MusicPlayer, Song
from models.utils.errors import SearchingException



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

    async def load_player(self, interaction: discord.Interaction, default: discord.VoiceChannel | None = None) -> MusicPlayer:
        assert interaction.guild is not None
        channel: discord.VoiceChannel

        if interaction.guild.id in self.players:
            if self.players[interaction.guild.id].voice_client is not None:
                return self.players[interaction.guild.id]
            
            if default is None:
                for vc in interaction.guild.voice_channels:
                    if vc.name.lower() == 'viber':
                        default = vc
                        break
                else:
                    default = interaction.guild.voice_channels[0]
            await self.players[interaction.guild.id].connect(default) # type: ignore

        
        for channel in interaction.guild.voice_channels:
            if channel in self.client.voice_clients:
                self.players[interaction.guild.id] = MusicPlayer.load(interaction.guild, default or channel) # type: ignore
                break
        else:
            channel = default or interaction.user.voice.channel # type: ignore[valid-type]
            self.players[interaction.guild.id] = await MusicPlayer.create(interaction.guild, channel)

        return self.players[interaction.guild.id]

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

    @commands.Cog.listener()
    async def on_error(self, interaction: discord.Interaction, error: slash.CommandInvokeError):
        await self.send_me(f"There's been an error on command {interaction.command.name}.\nError: {error.__class__.__name__}\n           {error}.") # type: ignore
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

    @slash.command(name='join', description='Connects to a voice channel')
    @slash.check(lambda interaction: interaction.guild is not None)
    @slash.describe(channel='The channel to which you want the bot to connect')
    async def connect(self, interaction: discord.Interaction, channel: discord.VoiceChannel | None = None):
        assert not isinstance(interaction.user, discord.User) and interaction.guild is not None
        _channel: discord.VoiceChannel
        
        await interaction.response.defer()
        if channel is None:
            if not self.can_connect(interaction):
                await self.send_error_message(interaction, cause='Could not connect to a voice channel, try to specify one or connect to one.', ephemeral=True)
                return
            _channel = interaction.user.voice.channel # type: ignore[valid-type]
        else:
            _channel = channel

        await self.load_player(interaction, _channel)
        await interaction.followup.send(f'Connected to {_channel.mention}')


    @slash.command(name='play', description='Plays a song in the server.')
    @slash.check(lambda interaction: isinstance(interaction.channel, discord.TextChannel))
    @slash.describe(reference='A song reference')
    async def play(self, interaction: discord.Interaction, reference: str, choose: bool = False):
        assert not isinstance(interaction.user, discord.User) and interaction.guild is not None

        await interaction.response.defer()
        player = await self.load_player(interaction)

        if player.sleeping and Song.cached(reference) and not choose:
            url = Song.load_cache(reference)
            await player.add_cached_song(url, reference, interaction)
            return

        try:
            if choose:
                song = await choice(interaction, reference, playable=True)
            else:                    
                song = search(reference, playable=True)[0]
        except SearchingException as e:
            await self.send_error_message(interaction, e, ephemeral=True) # type: ignore
            return
        await interaction.followup.send('Added to queue.', embed=song.embed)
        await player.add_song(song, interaction.user)

    @slash.command(name='pause', description='Pauses the song the bot is playing.')
    @slash.check(lambda interaction: isinstance(interaction.channel, discord.TextChannel))
    async def pause(self, interaction: discord.Interaction) -> None:
        assert interaction.guild is not None

        if interaction.guild.id not in self.players: 
            await interaction.response.send_message('There is no active player in this server.', ephemeral=True)
            return

        player = self.players[interaction.guild.id]
        await player.pause()
        await interaction.response.send_message('Player paused.')

    @slash.command(name='stop', description='Stops the player from playing.')
    @slash.check(lambda interaction: isinstance(interaction.channel, discord.TextChannel))
    async def stop(self, interaction: discord.Interaction) -> None:
        assert interaction.guild is not None

        if interaction.guild.id not in self.players: 
            await interaction.response.send_message('There is no active player in this server.', ephemeral=True)
            return

        player = self.players[interaction.guild.id]
        await player.stop()
        await interaction.response.send_message('Player stopped.')

    @slash.command(name='leave', description='Disconnects from the voice channel.')
    @slash.check(lambda interaction: interaction.guild is not None)
    async def disconnect(self, interaction: discord.Interaction):
        assert interaction.guild is not None

        if interaction.guild.id not in self.players:
            await interaction.response.send_message("I'm not currently connected to any voice channel.", ephemeral=True)
            return

        player = self.players[interaction.guild.id]
        channel = player.voice_client.channel
        await player.disconnect()
        await interaction.response.send_message(f'Disconnected from {channel.mention}')

    @slash.command(name='queue', description='Sends a queue embed')
    @slash.check(lambda interaction: interaction.guild is not None)
    async def queue(self, interaction: discord.Interaction):
        assert interaction.guild is not None
       
        if interaction.guild.id not in self.players or len(self.players[interaction.guild.id].queue) == 0:
            await interaction.response.send_message("I'm not currenly streaming any music.", ephemeral=True)
            return 
        
        embed = discord.Embed(
            title="Queue",
            color=discord.Color.orange()
        )
        for song, _, _ in self.players[interaction.guild.id].queue:
            embed.add_field(name=song.title, value=song.author, inline=False) # type: ignore
        
        await interaction.response.send_message(embed=embed)