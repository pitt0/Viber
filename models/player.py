import asyncio
import discord
import random

from .song import Song, search
from .utils import FFMPEG_OPTIONS

User = discord.Member | discord.User

class VPlayer(discord.ui.View):

    children: list[discord.ui.Button]
    message: discord.Message

    def __init__(self, player: 'MusicPlayer'):
        super().__init__(timeout=None)
        self.__player = player
        self.message = None # type: ignore

    def destroy(self) -> None:
        self.message = None # type: ignore

    @discord.ui.button(emoji='⏪', disabled=True)
    async def previous(self, interaction: discord.Interaction, _) -> None:
        self.__player.play_previous = True
        await self.__player.stop(force=False)
        await interaction.response.send_message(f'Song replayed.', ephemeral=True)
    
    @discord.ui.button(emoji='⏸️')
    async def play_pause(self, interaction: discord.Interaction, _) -> None:
        if self.__player.playing:
            await self.__player.pause()
            await interaction.response.send_message(f'Song paused.', ephemeral=True)
        else:
            await self.__player.resume()
            await interaction.response.send_message(f'Song resumed.', ephemeral=True)

    @discord.ui.button(emoji='⏩', disabled=True)
    async def next(self, interaction: discord.Interaction, _) -> None:
        await self.__player.stop(force=False)
        await interaction.response.send_message(f'Song skipped.', ephemeral=True)

    @discord.ui.button(emoji='💟', disabled=True)
    async def like(self, interaction: discord.Interaction, _) -> None:
        # TODO: Add the song to user's favourites
        pass

    @discord.ui.button(emoji='⏹️', row=1)
    async def stop(self, interaction: discord.Interaction, _) -> None:
        await self.__player.stop()
        await interaction.response.send_message(f'Player stopped.', ephemeral=True)

    @discord.ui.button(emoji='🔀', row=1, disabled=True)
    async def shuffle(self, interaction: discord.Interaction, _) -> None:
        song = self.__player.queue.pop(0)
        random.shuffle(self.__player.queue)
        self.__player.queue.insert(0, song)
        await interaction.response.send_message(f'Queue shuffled.', ephemeral=True)

    @discord.ui.button(emoji='🔁', row=1)
    async def loop(self, interaction: discord.Interaction, _) -> None:
        await self.__player.set_loop(interaction, self.__player.loop + 1 if self.__player.loop != 2 else 0)

        

class MusicPlayer:
    
    __slots__ = (
        'guild',
        'channel',
        'voice_client',

        'loop',
        'player',

        'queue',
        'cache',
        'play_previous',

        '__searching',
        '__playing',
        '__trick_paused',

    )

    guild: discord.Guild
    channel: discord.TextChannel
    voice_client: discord.VoiceClient
    queue: list[tuple[Song | tuple[discord.Interaction, str, str], discord.FFmpegOpusAudio, User]]
    cache: list[tuple[Song, discord.FFmpegOpusAudio, User]]
    play_previous: bool

    loop: int
    player: VPlayer

    __searching: bool
    __playing: asyncio.Future[bool]

    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.queue = []
        self.cache = []

        self.player = None # type: ignore

        self.__prepare()
        self.__trick_paused = False
        self.play_previous = False
        self.loop = 0

        self.__searching = False

    @classmethod
    def load(cls, guild: discord.Guild, voice_client: discord.VoiceClient) -> 'MusicPlayer':
        self = cls(guild)
        self.voice_client = voice_client
        return self
    
    @classmethod
    async def create(cls, guild: discord.Guild, voice_channel: discord.VoiceChannel) -> 'MusicPlayer':
        self = cls(guild)
        for channel in guild.channels:
            if channel.name == '▶viber':
                self.channel = channel # type: ignore
                break
        else:
            self.channel = await guild.create_text_channel('▶viber')
        
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
        song = self.queue[0][0]
        assert isinstance(song, Song)
        requester = self.queue[0][2]
        _e = discord.Embed(
            title=song.title,
            description=f'{song.album} • {song.author}',
            color=discord.Color.blue()
        )
        _e.set_thumbnail(url=song.thumbnail)
        _e.set_footer(text=f'Queued by {requester.display_name}', icon_url=requester.display_avatar)
        _e.add_field(name="Duration", value=song.duration)
        return _e

    @property
    def player_message(self) -> discord.Message:
        return self.player.message

    # private methods
    async def get_source(self, url: str) -> discord.FFmpegOpusAudio:
        return await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)

    async def __update_player(self, view: bool = False):
        self.player.previous.disabled = not len(self.cache) > 0
        self.player.next.disabled = not (len(self.queue) > 1 or self.loop == 1)
        self.player.shuffle.disabled = not len(self.queue) > 2
        if view:
            await self.player.message.edit(view=self.player)
        
    async def __reset(self) -> None:
        await self.voice_client.disconnect()
        self.voice_client = None # type: ignore
        self.__init__(self.guild)

    def __prepare(self):
        loop = asyncio.get_running_loop()
        self.__playing = loop.create_future()

    def __next(self, _) -> None:
        if len(self.queue) == 0:
            self.__stop()
            return

        if self.play_previous:
            song, _, requester = self.cache.pop(-1)
            self.queue.insert(0, (song, asyncio.run(self.get_source(song.source)), requester))
            self.play_previous = False

        match self.loop:
            case 0:
                self.cache.append(self.queue.pop(0)) # type: ignore
            case 1:
                self.cache.append(self.queue.pop(0)) # type: ignore
                if len(self.queue) == 0:
                    self.queue = [(song, asyncio.run(self.get_source(song.source)), requester) for song, _, requester in self.cache]
            case 2:
                song, _, requester = self.queue.pop(0)
                if len(self.cache) > 0 and self.cache[-1] != song:
                    self.cache.append(song) # type: ignore
                self.queue.insert(0, (song, asyncio.run(self.get_source(song.source)), requester)) # type: ignore
        
        self.__stop()

        if len(self.queue) == 0:
            return
    
    def __stop(self) -> None:
        if not self.__playing.done():
            self.__playing.set_result(False)

    # public methods
    async def wait(self):
        return await self.__playing

    async def set_loop(self, interaction: discord.Interaction, num: int):
        self.loop = num
        match num:
            case 0:
                self.player.loop.emoji = '🔁'
                self.player.loop.style = discord.ButtonStyle.grey
            case 1:
                self.player.loop.emoji = '🔁'
                self.player.loop.style = discord.ButtonStyle.blurple
            case 2:
                self.player.loop.emoji = '🔂'
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
            print('helo')
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

    async def add_song(self, song: Song, requester: User) -> None:
        print('Adding from reference')

        source = await self.get_source(song.source)
        self.queue.append((song, source, requester))
        if self.sleeping:
            await self.play()
        else:
          await self.__update_player()

    async def add_cached_song(self, url: str, reference: str, interaction: discord.Interaction) -> None:
        print('Adding from cache')
        
        source = await self.get_source(url)
        self.queue.append(((interaction, url, reference), source, interaction.user))
        if self.sleeping:
            await self.play()
        else:
            await self.__update_player()
            self.__searching = True
            song = search(reference)[0]
            song.source = url
            self.queue[-1] = (song, source, interaction.user)
            await interaction.followup.send('Added to Queue.', embed=song.embed)
            self.__searching = False

    async def play(self) -> None:
        if self.player is None:
            self.player = VPlayer(self)
        while len(self.queue) > 0:

            song, source, requester = self.queue[0]
            self.__prepare() # Sets self.__playing to True
            self.voice_client.play(source, after=self.__next)

            if not isinstance(song, Song): 
                if not self.__searching:
                    interaction, url, reference = song
                    song = search(reference)[0]
                    song.source = url
                    self.queue[0] = (song, source, requester)
                    await interaction.followup.send("Now playing.")

            await self.__update_player()
            if not self.player.message:
                self.player.message = await self.channel.send(embed=self.embed, view=self.player)
            else:
                await self.player.message.edit(embed=self.embed, view=self.player)
            
            await self.wait()

    async def pause(self,) -> None:
        self.voice_client.pause()
        self.player.play_pause.emoji = '▶️'
        await self.__update_player()

    async def resume(self,) -> None:
        self.voice_client.resume()
        self.player.play_pause.emoji = '⏸️'
        await self.__update_player()
    
    async def stop(self, force: bool = True) -> None:
        self.voice_client.stop()
        if force:
            self.queue = []
            self.player.destroy()
            self.__stop()
