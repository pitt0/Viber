import asyncio
import discord

from .queue import Queue
from .ui import PlayerUI

from models import FFMPEG_OPTIONS, USER
from models.songs import Track



class MusicPlayer:

    guild: discord.Guild
    channel: discord.TextChannel
    voice_client: discord.VoiceClient
    queue: Queue
    play_previous: bool

    previous: bool
    player: PlayerUI

    __playing: asyncio.Future[bool]

    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.queue = Queue()

        self.player = None # type: ignore

        self.previous = False
        self.__trick_paused = False


    @classmethod
    def load(cls, guild: discord.Guild, voice_client: discord.VoiceClient) -> "MusicPlayer":
        self = cls(guild)
        self.voice_client = voice_client
        return self
    
    @classmethod
    async def create(cls, guild: discord.Guild, voice_channel: discord.VoiceChannel) -> "MusicPlayer":
        self = cls(guild)
        for channel in guild.channels:
            if channel.name == "▶viber":
                self.channel = channel # type: ignore
                break
        else:
            self.channel = await guild.create_text_channel("▶viber")

        self.voice_client = await voice_channel.connect()
        return self

    @property
    def playing(self) -> bool:
        return self.voice_client.is_playing()

    @property
    def paused(self) -> bool:
        return self.voice_client.is_paused()

    @property
    def sleeping(self) -> bool:
        return not (self.playing or self.paused)

    @property
    def embed(self) -> discord.Embed:
        song, _, requester = self.queue.current
        _e = song.embed
        _e.color = discord.Colour.blue()
        _e.set_footer(text=f"Queued by {requester.display_name}", icon_url=requester.display_avatar)
        return _e

    # private methods
    async def get_source(self, url: str) -> discord.FFmpegOpusAudio:
        return await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)

    async def __update_player(self, update: bool = False) -> None:
        self.player.previous.disabled = not self.queue.can_previous()
        self.player.next.disabled = not self.queue.can_next()
        self.player.shuffle.disabled = not self.queue.can_shuffle()

        if update:
            await self.player.message.edit(view=self.player)

    async def __reset(self) -> None:
        await self.voice_client.disconnect()
        self.voice_client = None # type: ignore
        self.__init__(self.guild)

    def __prepare(self) -> None:
        loop = asyncio.get_running_loop()
        self.__playing = loop.create_future()

    def __next(self, _) -> None:
        if self.queue.done():
            self.__stop()
            return

        if self.previous:
            self.queue.previous()
        else:
            self.queue.next()

        self.__stop()

        if self.queue.done():
            return
    
    def __stop(self) -> None:
        if not self.__playing.done():
            self.__playing.set_result(False)

    # public methods
    def go_back(self) -> None:
        self.previous = True

    async def wait(self) -> bool:
        return await self.__playing

    async def set_loop(self, interaction: discord.Interaction, num: int) -> None:
        self.queue.loop = num
        
        match num:
            case 0:
                self.player.loop.emoji = "🔁"
                self.player.loop.style = discord.ButtonStyle.grey
            case 1:
                self.player.loop.emoji = "🔁"
                self.player.loop.style = discord.ButtonStyle.blurple
            case 2:
                self.player.loop.emoji = "🔂"
                self.player.loop.style = discord.ButtonStyle.blurple

        await interaction.response.edit_message(view=self.player)

    async def connect(self, vc: discord.VoiceChannel) -> None:
        try:
            self.voice_client = await vc.connect()
        except discord.ClientException:
            await self.voice_client.move_to(vc)
        
    async def disconnect(self) -> None:
        await self.stop()
        await self.__reset()

    async def voice_update(self, before: discord.VoiceState, after: discord.VoiceState) -> None:
        assert self.voice_client is not None

        if after.channel is None:
            print("helo")
            return await self.__reset()

        if self.playing:
            print(after.channel.members)
            if len(after.channel.members) == 1 or all(member.bot or member.voice.deaf for member in after.channel.members): # type: ignore
                await self.pause()
                self.__trick_paused = True
                print("Paused. Cause: Members in a voice channel were either all deafened or all bot.")

        elif self.paused:
            if before.channel is not None:
                if self.__trick_paused:
                    self.__trick_paused = False
                    await self.resume()
                    print("Resumed.")

    async def add_song(self, song: Track, requester: USER) -> None:
        source = await self.get_source(song.source)
        self.queue.append((song, source, requester))
        if self.sleeping:
            await self.play()
        else:
            await self.__update_player()

    async def play(self) -> None:
        if self.player is None:
            self.player = PlayerUI(self)

        while not self.queue.done():
            # NOTE: Preferred to use a while so if a song is added or removed the queue doesn't skip anything

            _, source, _ = self.queue.current
            self.__prepare() # Creates the task
            self.voice_client.play(source, after=self.__next)

            await self.__update_player()
            if not self.player.message:
                self.player.message = await self.channel.send(embed=self.embed, view=self.player)
            else:
                await self.player.message.edit(embed=self.embed, view=self.player)
            
            await self.wait()

    async def pause(self,) -> None:
        self.voice_client.pause()
        self.player.play_pause.emoji = "▶️"
        await self.__update_player()

    async def resume(self,) -> None:
        self.voice_client.resume()
        self.player.play_pause.emoji = "⏸️"
        await self.__update_player()
    
    async def stop(self, force: bool = True) -> None:
        self.voice_client.stop()
        if force:
            self.queue = Queue()
            self.player.destroy()
            self.__stop()
