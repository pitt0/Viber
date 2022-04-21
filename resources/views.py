from typing import TYPE_CHECKING, Any, Callable, Coroutine
from discord.ui import TextInput

import discord

from .song import Song
from .playlist import Playlist


class MPassword(discord.ui.Modal):
    def __init__(self, playlist: Playlist, action: Callable[[discord.Interaction], Coroutine[Any, Any, None]], retry: bool = False):
        if retry:
            super().__init__(title='Incorrect Password. Retry.')
        else:
            super().__init__(title='Insert Password')
    
        self.password = TextInput(label='Password', placeholder="Insert Playlist's password", required=True)

        self.playlist = playlist
        self.action = action


    async def on_submit(self, interaction: discord.Interaction):
        if self.password != self.playlist.password:
            await interaction.response.send_modal(MPassword(self.playlist, self.action, retry=True))
            return

        await self.action(interaction)


class MSetPassword(discord.ui.Modal):
    def __init__(
        self, 
        playlist: Playlist, 
        action: Callable[[discord.Interaction], Coroutine[Any, Any, None]], 
        title: str = 'Set a new Password',
        **default
    ) -> None:

        super().__init__(title=title)

        self.playlist = playlist
        self.action = action

        self.old_password = None

        Input = TextInput['MSetPassword']

        if self.playlist.password is not None:
            self.old_password: Input | None = TextInput(label='Insert Old Password', placeholder='Password', required=True, default=default['old_password'])
        self.new_password: Input = TextInput(label='Set Password', placeholder='Password', required=True, min_length=8, default=default['new_password'])
        self.repeat: Input = TextInput(label='Repeat Password', placeholder='Password', required=True, min_length=8, default=default['repeat'])

    
    async def on_submit(self, interaction: discord.Interaction):
        if self.old_password is not None and self.old_password != self.playlist.password:
            await interaction.response.send_modal(MSetPassword(self.playlist, self.action, 'Incorrect Password. Please Retry.', new_password=self.new_password, repeat=self.repeat))
            return

        if self.new_password != self.repeat:
            await interaction.response.send_modal(MSetPassword(self.playlist, self.action, 'Passwords Must Match', old_pasword=self.old_password, new_password=self.new_password))
            return

        await self.action(interaction)


class MRenamePlaylist(discord.ui.Modal):
    def __init__(self, playlist: Playlist, retry: bool = False, name_default: str | None = None):
        if retry:
            super().__init__(title='Wrong Password. Try again.')
        else:
            super().__init__(title='Rename this playlist.')

        self.playlist = playlist
        self.password = None
        Input = TextInput['MRenamePlaylist']
        self.new_name: Input = TextInput(label='New Name', placeholder='Name', required=True, min_length=2, max_length=20, default=name_default)
        if self.playlist.private:
            self.password: Input | None = TextInput(label='Insert Password', placeholder='Password', required=True, min_length=8)


    async def on_submit(self, interaction: discord.Interaction):
        if self.password is not None and self.password.value != self.playlist.password:
            await interaction.response.send_modal(MRenamePlaylist(self.playlist, True, name_default=self.new_name.value))
            return
        if self.new_name.value is None:
            return
        self.playlist.rename(self.new_name.value)
        await interaction.response.send_message(f"Playlist's name has been changed to `{self.new_name}`")


class MAddSong(discord.ui.Modal):
    
    if TYPE_CHECKING:
        password: TextInput['MAddSong'] | None
        reference: TextInput['MAddSong']

    def __init__(self, playlist: Playlist, retry: bool = False, song_default: str | None = None):
        if retry:
            super().__init__(title='Wrong Password. Please retry.')
        else:
            super().__init__(title='Add a Song')

        self.playlist = playlist

        self.password = None
        self.reference = TextInput(label='Song Reference', placeholder='Song', required=True, default=song_default)
        if self.playlist.private:
            self.password = TextInput(label='Insert Password', placeholder='Password', required=True)

    async def on_submit(self, interaction: discord.Interaction):
        if self.password is not None and self.password != self.playlist.password:
            await interaction.response.send_modal(MAddSong(self.playlist, True, song_default=self.reference.value))
            return

        song = await Song.from_data(str(self.reference), interaction) # TextInput's __str__ method returns its value
        if song is None:
            return 

        self.playlist.add_song(song)
        await interaction.followup.send(f'`{song.title} by {song.author}` added to playlist')

class MRemoveSong(discord.ui.Modal):
    
    if TYPE_CHECKING:
        password: TextInput['MRemoveSong'] | None
        reference: TextInput['MRemoveSong']

    def __init__(self, playlist: Playlist, retry: bool = False, song_default: str | None = None):
        if retry:
            super().__init__(title='Wrong Password. Please retry.')
        else:
            super().__init__(title='Add a Song')

        self.playlist = playlist

        self.password = None
        self.reference = TextInput(label='Song Reference', placeholder='Song', required=True, default=song_default)
        if self.playlist.private:
            self.password = TextInput(label='Insert Password', placeholder='Password', required=True)

    async def on_submit(self, interaction: discord.Interaction):
        if self.password is not None and self.password != self.playlist.password:
            await interaction.response.send_modal(MAddSong(self.playlist, True, song_default=self.reference.value))
            return

        song = await Song.from_data(str(self.reference), interaction)
        if song is None:
            return 
        try:
            self.playlist.remove_song(song)
        except IndexError:
            await interaction.followup.send(f'`{song.title} by {song.author}` is not in the playlist')
        else:
            await interaction.followup.send(f'`{song.title} by {song.author}` added to playlist')



class VPlaylist(discord.ui.View):

    def __init__(self, playlist: Playlist):
        super().__init__()

        self.playlist = playlist
        children: list[discord.ui.Button] = self.children # type: ignore
        if self.playlist.private:
            children[0].label = 'Lock'
        else:
            children[0].label = 'Unlock'
    
    async def unlock(self, interaction: discord.Interaction) -> None:
        self.playlist.unlock()
        success = discord.Embed(title='Success!', description=f'Playlist `{self.playlist.name}` successfully unlocked!', color=discord.Color.og_blurple())
        if interaction.response.is_done():
            await interaction.followup.send(embed=success)
        else:
            await interaction.response.send_message(embed=success)

    async def lock(self, interaction: discord.Interaction) -> None:
        self.playlist.lock()
        success = discord.Embed(title='Success!', description=f'Playlist `{self.playlist.name}` successfully locked!', color=discord.Color.og_blurple())
        if interaction.response.is_done():
            await interaction.followup.send(embed=success)
        else:
            await interaction.response.send_message(embed=success)

    async def delete(self, interaction: discord.Interaction) -> None:
        self.playlist.delete()
        success = discord.Embed(title='Success!', description=f'Playlist `{self.playlist.name}` successfully deleted!', color=discord.Color.og_blurple())
        if interaction.response.is_done():
            await interaction.followup.send(embed=success)
        else:
            await interaction.response.send_message(embed=success)

    @discord.ui.button(label='Lock')
    async def lock_playlist(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.playlist.private:
            await interaction.response.send_modal(MPassword(self.playlist, action=self.unlock))
        
        else:
            if self.playlist.password is None:
                await interaction.response.send_modal(MSetPassword(self.playlist, action=self.lock))
            else:
                self.playlist.lock()
                await interaction.response.send_message(embed=discord.Embed(title='Success!', description=f'Playlist `{self.playlist.name}` has been locked', color=discord.Color.og_blurple()))

    @discord.ui.button(label='Rename')
    async def rename_playlist(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MRenamePlaylist(self.playlist))

    @discord.ui.button(label='Add Song')
    async def add_song(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MAddSong(self.playlist))

    @discord.ui.button(label='Remove Song')
    async def remove_song(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MRemoveSong(self.playlist))

    @discord.ui.button(label='Delete')
    async def delete_playlist(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MPassword(self.playlist, self.delete))

    # TODO: Add a change password method


class VAdviceList(discord.ui.View):

    def __init__(self, embeds: list[discord.Embed]):
        super().__init__()
        self.embeds = embeds

        self.index = 0

    @property
    def index(self) -> int:
        return self.__index

    @index.setter
    def index(self, value: int):
        assert not (0 <= value <= len(self.embeds) - 1), f'Value set for index: {value}'

        self.current_song = self.embeds[value]
        children: list[discord.ui.Button] = self.children # type: ignore

        children[0].disabled = children[1].disabled = not value
        children[2].disabled = children[3].disabled = value == len(self.embeds) -1

        self.__index = value

    @discord.ui.button(label='<<')
    async def _to_first(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = 0

        await interaction.response.edit_message(embed=self.current_song, view=self)

    @discord.ui.button(label='<')
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index -= 1

        await interaction.response.edit_message(embed=self.current_song, view=self)

    @discord.ui.button(label='>')
    async def fowrard(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index += 1

        await interaction.response.edit_message(embed=self.current_song, view=self)

    @discord.ui.button(label='>>')
    async def _to_last(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = len(self.embeds) - 1

        await interaction.response.edit_message(embed=self.current_song, view=self)
