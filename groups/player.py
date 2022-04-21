from discord import app_commands as slash
from discord.ext import commands

import discord

from resources import Song, ESong, MusicPlayer
from resources import GUILD_ID
from resources.utils import youtube






class Player(slash.Group):

    def __init__(self, client: discord.Client):
        super().__init__()
        self.client = client
        self.players: dict[GUILD_ID, MusicPlayer] = {}


    async def send_me(self, text: str) -> None:
        me = await self.client.fetch_user(648939655579828226)
        await me.send(text)

    async def send_error_message(self, cause: str, ephemeral: bool, interaction: discord.Interaction) -> None:
        _embed = discord.Embed(
            title='Something went wrong',
            description=cause,
            color=discord.Color.dark_red()
        )
        if interaction.response.is_done():
            await interaction.followup.send(embed=_embed, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(embed=_embed, ephemeral=ephemeral)

    async def create_player(self, guild: discord.Guild, voice: discord.VoiceChannel | None) -> None:
        if guild.id not in self.players:
            _player = MusicPlayer(guild)
            self.players[guild.id] = _player

        else:
            _player = self.players[guild.id]

        await _player.connect(voice or _player.voiceClient.channel) # type: ignore
        return


    async def search_song(self, reference: str) -> Song | None:
        if reference.startswith('http'):
            song = Song.from_youtube(reference)
            if song is None:
                return 
        else:
            urls = youtube.search_urls(reference)
            if urls is None:
                return
            # TODO: Add an IA that parses through all the urls to see if is there any preferred one
            song = Song.from_youtube(urls[0])
        
        return song

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
        if isinstance(interaction.user, discord.User): # should never happen
            await self.send_me(f'`interaction.user` was `discord.User`.\nServer: {interaction.guild}\nUser: {interaction.user}')
            return
        
        if channel is None:
            if interaction.user.voice is None or not isinstance(interaction.user.voice.channel, discord.VoiceChannel):
                await self.send_error_message('Could not connect to a voice channel, try to specify one or connect to one.', True, interaction)
                return
            channel = interaction.user.voice.channel

        await self.create_player(interaction.guild, channel) # type: ignore 


    @slash.command(name='play', description='Plays a song in the server.')
    @slash.check(lambda interaction: isinstance(interaction.channel, discord.TextChannel))
    @slash.describe(reference='A song reference')
    async def play(self, interaction: discord.Interaction, reference: str):
        assert interaction.guild is not None

        if isinstance(interaction.user, discord.User): # should never happen
            await self.send_me(f'`interaction.user` was `discord.User`.\nServer: {interaction.guild}\nUser: {interaction.user}')
            return 

        await interaction.response.defer()

        try:
            await self.create_player(interaction.guild, interaction.user.voice.channel if interaction.user.voice else None) # type: ignore[valid-type]
        except Exception as e:
            raise e

        if reference.startswith('http') and ('youtube.com' not in reference and 'youtu.be' not in reference):
            await interaction.followup.send('I only accept youtube links.', ephemeral=True)
            return
        
        song = await self.search_song(reference)
        if song is None:
            await interaction.followup.send('Could not find anything.')
            return

        song_embed = ESong(song, False)
        await interaction.followup.send('Now playing.', embed=song_embed)
        await self.players[interaction.guild.id].add_song(song)