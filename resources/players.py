from typing import TYPE_CHECKING

import asyncio
import discord

from .song import Song
from .utils import FFMPEG_OPTIONS

class Sound: pass

class _BasePlayer:

    if TYPE_CHECKING:
        guild: discord.Guild
        voiceClient: discord.VoiceClient

    
    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, self.__class__) and __o.guild.id == self.guild.id

    def __del__(self) -> None:
        assert self.voiceClient is not None
        asyncio.run(self.voiceClient.disconnect())


class AudioPlayer(_BasePlayer):

    __slots__ = (
        'voiceClient',
        'guild',
        'queue',

        '__playing'
        )

    if TYPE_CHECKING:
        voiceClient: discord.VoiceClient | None
        guild: discord.Guild

    def __init__(self, guild):
        self.guild = guild
        self.voiceClient = None
        self.queue = []

        self.__playing: asyncio.Future[bool] | None = None

    
    # properties
    @property
    def playing(self) -> bool:
        assert self.voiceClient is not None
        return self.voiceClient.is_playing()

    @property
    def paused(self) -> bool:
        assert self.voiceClient is not None
        return self.voiceClient.is_paused()

    @property
    def not_sleeping(self) -> bool:
        assert self.voiceClient is not None
        return self.voiceClient.is_playing() or self.voiceClient.is_paused()
    

    # protected methods
    async def _create_playing_loop(self):
        loop = asyncio.get_running_loop()
        self.__playing = loop.create_future()

    async def _wait(self):
        """Waits for a sound to stop playing."""
        assert self.__playing is not None
        return await self.__playing

    def _end_playing(self, _) -> None:
        assert self.__playing is not None
        self.__playing.set_result(False)
        self.__playing = None

    async def _prepare(self):
        await self._create_playing_loop()
    
    # public methods
    async def connect(self, voice: discord.VoiceChannel) -> None:
        if self.voiceClient is None:
            self.voiceClient = await voice.connect()
        else:
            await self.voiceClient.move_to(voice)

    async def voice_update(self, before: discord.VoiceChannel, after: discord.VoiceChannel):
        raise NotImplemented()

    async def add_sound(self, sound: Sound) -> None:
        source = await discord.FFmpegOpusAudio.from_probe(sound.source, **FFMPEG_OPTIONS) # type: ignore
        self.queue.append((sound, source))



class MusicPlayer(AudioPlayer):
    
    __slots__ = (
        '__trick_paused',
    )

    if TYPE_CHECKING:
        queue: list[tuple[Song, discord.FFmpegOpusAudio]]

    def __init__(self, guild: discord.Guild):
        super().__init__(guild)

        self.__trick_paused = False


    # private methods
    async def __reset(self) -> None:
        assert self.voiceClient is not None
        await self.voiceClient.disconnect()
        self.__init__(self.guild)

    async def __load_to_cache(self, song: Song) -> None:
        ...


    # protected methods
    async def _prepare(self, song: Song):
        await self.__load_to_cache(song)
        await super()._prepare()


    # public methods
    async def voice_update(self, before: discord.VoiceState, after: discord.VoiceState) -> None:
        assert self.voiceClient is not None

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
       
        if not self.not_sleeping:
            await self.play()

    async def play(self,) -> None:
        assert self.voiceClient is not None
        while self.queue:

            song, source = self.queue[0]

            await self._prepare(song) # Sets self.__playing to True and loads the song to cache
            self.voiceClient.play(source, after=self._end_playing)  # type: ignore
            await self._wait()

    async def pause(self,) -> None:
        assert self.voiceClient is not None
        self.voiceClient.pause()

    async def resume(self,) -> None:
        assert self.voiceClient is not None
        self.voiceClient.resume() 