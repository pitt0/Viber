import discord
from discord.ext import commands

from api.cache import SongCache
from api.connections import JSONConnection
from api.local import SongsAPI as LocalSongsAPI
from api.web import SongsAPI as WebSongsAPI
from models import ExternalSong, LocalSong, Song
from player import MusicPlayer
from resources import Time
from typings import GuildID
from ui import Selector


class FailableCog(commands.Cog):

    @commands.Cog.listener()
    async def on_command_error(self, context: commands.Context, error: Exception) -> None:
        if context.command is None:
            dev_message = "There's been an unknown error."
            usr_message = "There's been an unknown error, please try again or contact the developer."
        else:
            dev_message = f"There's been an error on command _{context.command.name}_"
            usr_message = f"There's been an error trying to run command _{context.command.name}_"

        dev_message += (
            "\n"
            f"\n*Error: _{error.__class__.__name__}_*"
            "\n```"
            f"\n{error.__context__}"
            "\n```"
        )

        with JSONConnection('devs.json') as devs:
            for dev_id in devs:
                dev = await context.bot.fetch_user(dev_id)
                await dev.send(dev_message)

        _error_embed = discord.Embed(
            title="**:x: Error**",
            description=usr_message
        ).set_footer(text="Contact the dev @coolermustacho")

        await context.send(embed=_error_embed)


class Players(dict[GuildID, MusicPlayer]):
    """Represents the wrapper of every instance of player of the bot per guild."""

    async def load_context(self, context: commands.Context[commands.Bot], default: discord.VoiceChannel | None = None) -> MusicPlayer:
        assert context.guild is not None and context.author is discord.Member
        if context.guild.id in self:
            if self[context.guild.id].voice_client is not None:
                return self[context.guild.id]
            
            if default is None:
                # TODO - create a setting to set a default vc fallback, this is nonsense
                for vc in context.guild.voice_channels:
                    if vc.name.lower() == "viber":
                        default = vc
                        break
                else:
                    default = context.guild.voice_channels[0]
            await self[context.guild.id].connect(default)
        
        if (voice_connection := discord.utils.get(context.bot.voice_clients, guild=context.guild)) is not None:
            assert voice_connection is discord.VoiceClient
            self[context.guild.id] = MusicPlayer.load(context.guild, voice_connection.channel)

        vc = discord.utils.get(context.bot.voice_clients, guild=context.guild)
        vc.is_connected()
        for channel in context.guild.voice_channels:
            if channel in context.bot.voice_clients:
                self[context.guild.id] = MusicPlayer.load(context.guild, await (default or channel).connect())
                break
        else:




    async def load_interaction(self, context: discord.Interaction, default: discord.VoiceChannel | None = None) -> MusicPlayer:
        if context.guild.id in self:
            if self[context.guild.id].voice_client is not None:
                return self[context.guild.id]

            if default is None:
                for vc in context.guild.voice_channels:
                    if vc.name.lower() == "viber":
                        default = vc
                        break
                else:
                    default = context.guild.voice_channels[0]
            await self[context.guild.id].connect(default)

        for channel in context.guild.voice_channels:
            if channel in context.bot.voice_clients:
                self[context.guild.id] = MusicPlayer.load(context.guild, default or channel)
                break
        else:
            if not context.author.voice or not isinstance(context.author.voice.channel, discord.VoiceChannel):
                raise ValueError
            channel = default or context.author.voice.channel
            self[context.guild.id] = await MusicPlayer.create(context.guild, channel)

        return self[context.guild.id]

async def choose_song(context: commands.Context, query: str, choices: list[ExternalSong]) -> LocalSong:
    view = Selector(choices)
    await context.send(embed=choices[0].embed, view=view)
    await view.wait()
    return await LocalSongsAPI.upload(view.song, query)

async def search_song(context: commands.Context, query: str, choose: bool) -> Song:
    # TODO: test and remove logs
    if query.startswith('http'):
        print(f'[{Time.now()}] Url found, loading.')
        if (song := await WebSongsAPI.load(query)) is None:
            print(f'[{Time.now()}] Url returned nothing, raising Exception.')
            raise ValueError
        print(f'[{Time.now()}] Song found, exiting.')
        return song

    if choose:
        print(f'[{Time.now()}] User set flag choose.')
        if (choices := await WebSongsAPI.search(query)) is None:
            raise ValueError
        print(f'[{Time.now()}] Searching "{query}" returned {len(choices)} results.')
        print(f'[{Time.now()}] Letting user choose song.')
        return await choose_song(context, query, choices)

    else:
        print(f'[{Time.now()}] Skipping choice step.')
        if (song_id := SongCache.load(query)) is not None:
            print(f'[{Time.now()}] "{query}" is present in the cache, loading from database.')
            return await LocalSongsAPI.get_song(song_id)

        else:
            print(f'[{Time.now()}] "{query}" is not present in the database, searching.')
            if (song := await WebSongsAPI.search(query, 1)) is None:
                raise ValueError
            print(f'[{Time.now()}] Song found, continuing.')
            return song[0]
