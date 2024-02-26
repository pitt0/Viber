import discord
from .utils import FailableCog, Players, search_song
from discord import app_commands as slash
from discord.ext import commands
from models import Song
from player import MusicPlayer


class Player(FailableCog):

    def __init__(self) -> None:
        self.players = Players()

    @staticmethod
    def can_connect_to_user_vc(user: discord.Member) -> bool:
        return user.voice is not None and isinstance(user.voice.channel, discord.VoiceChannel)

    def get_guild_player(self, guild: discord.Guild) -> MusicPlayer:
        return self.players[guild.id]

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        if member.guild.id not in self.players:
            return
        _player = self.get_guild_player(member.guild)
        await _player.voice_update(before, after)

    @commands.hybrid_command(name="join", description="Connects to a voice channel")
    @commands.guild_only()
    @slash.describe(channel="The channel to which you want the bot to connect")
    async def connect(self, context: commands.Context, channel: discord.VoiceChannel | None = None) -> None:
        assert isinstance(context.author, discord.Member) and context.guild is not None  # NOTE: typechecking
        _channel: discord.VoiceChannel

        if channel is None:
            if not self.can_connect_to_user_vc(context.author):
                return
            _channel = context.author.voice.channel  # type: ignore
        else:
            _channel = channel

        await self.players.load(context, _channel)
        await context.send(f"Connected to {_channel.mention}")

    @commands.hybrid_command(name="play", description="Plays a song in the server.")
    @commands.guild_only()
    @slash.describe(query="A song reference")
    async def play(self, context: commands.Context[commands.Bot], query: str, choose: bool = False) -> None:
        assert isinstance(context.author, discord.Member) and context.guild is not None  # NOTE: typechecking
        player = await self.players.load(context.guild, context.author)
        song = await search_song(context, query, choose)
        await context.send("Added to queue.", embed=song.embed)
        await player.add_song(song, context.author)

    @commands.hybrid_command(name="pause", description="Pauses the song the bot is playing.")
    @commands.guild_only()
    async def pause(self, context: commands.Context) -> None:
        assert context.guild is not None  # NOTE: manual typechecking
        if context.guild.id not in self.players:
            await context.send("There is no active player in this server.", ephemeral=True)
            return

        player = self.get_guild_player(context.guild)  # type: ignore[non-null]
        await player.pause()
        await context.send("Player paused.")

    @commands.hybrid_command(name="stop", description="Stops the player from playing.")
    @commands.guild_only()
    async def stop(self, context: commands.Context) -> None:
        assert context.guild is not None  # NOTE: typechecking
        if context.guild.id not in self.players:
            await context.send("There is no active player in this server.", ephemeral=True)
            return

        player = self.get_guild_player(context.guild)  # type: ignore
        await player.stop()
        await context.send("Player stopped.")

    @commands.hybrid_command(name="leave", description="Disconnects from the voice channel.")
    @commands.guild_only()
    async def disconnect(self, context: commands.Context) -> None:
        assert context.guild is not None  # NOTE: typechecking
        if context.guild.id not in self.players:
            await context.send("I'm not currently connected to any voice channel.", ephemeral=True)
            return

        player = self.get_guild_player(context.guild)  # type: ignore[non-null]
        channel = player.voice_client.channel
        await player.disconnect()
        await context.send(f"Disconnected from {channel.mention}")

    @commands.hybrid_command(name="queue", description="Sends a queue embed")
    @commands.guild_only()
    async def queue(self, context: commands.Context) -> None:
        assert context.guild is not None  # NOTE: typechecking
        player = self.get_guild_player(context.guild)
        if context.guild.id not in self.players or not player.queue:
            await context.send("I'm not currenly streaming any music.", ephemeral=True)
            return

        await context.send(embed=player.queue.embed)

    @commands.hybrid_command(name="loop", description="Loops the queue.")
    @commands.guild_only()
    async def loop_queue(self, context: commands.Context) -> None:
        assert context.guild is not None  # NOTE: typechecking
        player = self.get_guild_player(context.guild)

        if context.guild.id not in self.players or not player.queue:
            await context.send("I'm not currently streaming any music.", ephemeral=True)
            return

        await player.set_loop(context, 1)
        await context.send("Queue looped.")

    @commands.hybrid_command(name="loop-song", description="Loops the current song.")
    @commands.guild_only()
    async def loop_song(self, context: commands.Context) -> None:
        assert context.guild is not None  # NOTE: typechecking
        player = self.get_guild_player(context.guild)
        if context.guild.id not in self.players or not player.queue:
            await context.send("I'm not currently streaming any music.", ephemeral=True)
            return

        await player.set_loop(context, 2)
        await context.send("Song looped.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Player(bot))
