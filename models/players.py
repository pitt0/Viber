import asyncio
import discord

from .song import Song
from .utils import FFMPEG_OPTIONS



class MusicPlayer:
    
    __slots__ = (
        'guild',
        'voice_client',
        
        'queue',

        '__playing',
        '__trick_paused',
    )

    guild: discord.Guild
    voice_client: discord.VoiceClient
    queue: list[tuple[Song, discord.FFmpegOpusAudio]]

    __playing: asyncio.Future[bool]

    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.queue = []


        self.__prepare()
        self.__trick_paused = False


    @property
    def playing(self) -> bool:
        return self.voice_client.is_playing()
    
    @property
    def paused(self) -> bool:
        return self.voice_client.is_paused()

    @property
    def sleeping(self) -> bool:
        return not (self.playing or self.paused)


    # private methods
    async def __reset(self) -> None:
        await self.voice_client.disconnect()
        del self.voice_client
        self.__init__(self.guild)

    async def __load_to_cache(self, song: Song) -> None:
        ...

    def __prepare(self):
        loop = asyncio.get_running_loop()
        self.__playing = loop.create_future()

    async def __wait(self):
        return await self.__playing

    def __stop(self) -> None:
        self.__playing.set_result(False)


    # public methods
    async def connect(self, vc: discord.VoiceChannel) -> None:
        try:
            self.voice_client = await vc.connect()
        except discord.ClientException:
            await self.voice_client.move_to(vc)

    async def voice_update(self, before: discord.VoiceState, after: discord.VoiceState) -> None:
        assert self.voice_client is not None

        if after.channel is None:
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

    async def add_song(self, song: Song) -> None:
        source = await discord.FFmpegOpusAudio.from_probe(song.source, **FFMPEG_OPTIONS)
        self.queue.append((song, source))
        if self.playing:
            return
       
        if self.sleeping:
            await self.play()

    async def play(self,) -> None:
        while self.queue:

            song, source = self.queue[0]

            self.__prepare() # Sets self.__playing to True and loads the song to cache
            self.voice_client.play(source, after=self.__stop())
            await self.__wait()

    async def pause(self,) -> None:
        self.voice_client.pause()

    async def resume(self,) -> None:
        self.voice_client.resume() 