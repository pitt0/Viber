from discord import app_commands as slash
from discord.ext import commands

import discord

from resources import JSONConnection
from resources import SearchingException

from models import SongsChoice
from models import YTMusicSong
from models import Players, MusicPlayer



class Player(slash.Group):

    def __init__(self, client: discord.Client) -> None:
        super().__init__()
        self.client = client
        self.players = Players()

    @staticmethod
    def can_connect(interaction: discord.Interaction) -> bool:
        assert not isinstance(interaction.user, discord.User)
        return interaction.user.voice is not None and isinstance(interaction.user.voice.channel, discord.VoiceChannel)

    def player(self, interaction: discord.Interaction) -> MusicPlayer:
        return self.players[interaction.guild.id] # type: ignore

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
                parent_name = ""
                if interaction.command.parent is not None:
                    parent_name = f"{interaction.command.parent.name} "
                full_name = parent_name + interaction.command.name
                dev_message = f"There's been an error on command _{full_name}_"
                usr_message = f"There's been an error trying to run command _{full_name}_"
            case slash.ContextMenu():
                dev_message = f"There's been an error on app command _{interaction.command.name}_"
                usr_message = f"There's been an error trying to run app command _{interaction.command.name}_"

        dev_message += (
            f"\n*Error: _{error.__class__.__name__}_*" +
            "\n```" + 
            f"\n{error}" +
            "\n```"
        )

        with JSONConnection('devs.json') as devs:
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


    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        guild: discord.Guild = member.guild
        
        if guild.id not in self.players: 
            return
        _player = self.players[guild.id]
        await _player.voice_update(before, after)

    @slash.command(name="join", description="Connects to a voice channel")
    @slash.check(lambda interaction: interaction.guild is not None)
    @slash.describe(channel="The channel to which you want the bot to connect")
    async def connect(self, interaction: discord.Interaction, channel: discord.VoiceChannel | None = None):
        assert not isinstance(interaction.user, discord.User) and interaction.guild is not None
        _channel: discord.VoiceChannel
        
        await interaction.response.defer()
        if channel is None:
            if not self.can_connect(interaction):
                # await self.send_error_message(interaction, cause="Could not connect to a voice channel, try to specify one or connect to one.", ephemeral=True)
                return
            _channel = interaction.user.voice.channel # type: ignore[valid-type]
        else:
            _channel = channel

        await self.players.load(interaction, _channel)
        await interaction.followup.send(f"Connected to {_channel.mention}")


    @slash.command(name="play", description="Plays a song in the server.")
    @slash.check(lambda interaction: isinstance(interaction.channel, discord.TextChannel))
    @slash.describe(reference="A song reference")
    async def play(self, interaction: discord.Interaction, reference: str, choose: bool = False):
        assert not isinstance(interaction.user, discord.User) and interaction.guild is not None

        await interaction.response.defer()
        player = await self.players.load(interaction)

        try:
            if choose:
                choice = SongsChoice.search(reference, YTMusicSong)
                song = await choice.choose(interaction)
            else:
                song = await YTMusicSong.find(reference)
        except SearchingException:
            # await self.send_error_message(interaction, e, ephemeral=True)
            return
        
        await interaction.followup.send("Added to queue.", embed=song.embed)
        await player.add_song(song, interaction.user) # type: ignore

    @slash.command(name="pause", description="Pauses the song the bot is playing.")
    @slash.check(lambda interaction: isinstance(interaction.channel, discord.TextChannel))
    async def pause(self, interaction: discord.Interaction) -> None:
        assert interaction.guild is not None

        if interaction.guild.id not in self.players: 
            await interaction.response.send_message("There is no active player in this server.", ephemeral=True)
            return

        player = self.player(interaction)
        await player.pause()
        await interaction.response.send_message("Player paused.")

    @slash.command(name="stop", description="Stops the player from playing.")
    @slash.check(lambda interaction: isinstance(interaction.channel, discord.TextChannel))
    async def stop(self, interaction: discord.Interaction) -> None:
        assert interaction.guild is not None

        if interaction.guild.id not in self.players: 
            await interaction.response.send_message("There is no active player in this server.", ephemeral=True)
            return

        player = self.player(interaction)
        await player.stop()
        await interaction.response.send_message("Player stopped.")

    @slash.command(name="leave", description="Disconnects from the voice channel.")
    @slash.check(lambda interaction: interaction.guild is not None)
    async def disconnect(self, interaction: discord.Interaction):
        assert interaction.guild is not None

        if interaction.guild.id not in self.players:
            await interaction.response.send_message("I'm not currently connected to any voice channel.", ephemeral=True)
            return

        player = self.player(interaction)
        channel = player.voice_client.channel
        await player.disconnect()
        await interaction.response.send_message(f"Disconnected from {channel.mention}")

    @slash.command(name="queue", description="Sends a queue embed")
    @slash.check(lambda interaction: interaction.guild is not None)
    async def queue(self, interaction: discord.Interaction):
        assert interaction.guild is not None
       
        player = self.player(interaction)

        if interaction.guild.id not in self.players or not player.queue:
            await interaction.response.send_message("I'm not currenly streaming any music.", ephemeral=True)
            return 
        
        await interaction.response.send_message(embed=player.queue.embed)

    @slash.command(name="loop", description="Loops the queue.")
    @slash.check(lambda interaction: interaction.guild is not None)
    async def loop_queue(self, interaction: discord.Interaction):
        assert interaction.guild is not None

        player = self.player(interaction)

        if interaction.guild.id not in self.players or not player.queue:
            await interaction.response.send_message("I'm not currently streaming any music.", ephemeral=True)
            return

        await player.set_loop(interaction, 1)
        await interaction.followup.send("Queue looped.")

    @slash.command(name="loop_song", description="Loops the current song.")
    @slash.check(lambda interaction: interaction.guild is not None)
    async def loop_song(self, interaction: discord.Interaction):
        assert interaction.guild is not None

        player = self.player(interaction)
        if interaction.guild.id not in self.players or not player.queue:
            await interaction.response.send_message("I'm not currently streaming any music.", ephemeral=True)
            return

        await player.set_loop(interaction, 2)
        await interaction.followup.send("Song looped.")