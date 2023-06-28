from discord import app_commands as slash
from discord.ui import TextInput
from typing import Callable, Coroutine

import discord
import random
import yarl

import ui
from models import LocalPlaylist, YouTubePlaylist, SpotifyPlaylist
from models import SongsChoice, PermissionLevel
from models import SpotifySong, LocalSong
from models import GuildLister, UserLister, Cached



# type Cache = list[tuple[int, str]]
# type LiveCache = Callable[[discord.Interaction, str], Cache]
Cache = list[tuple[int, str]]
LiveCache = Callable[[discord.Interaction, str], Cache]

def autocomplete(cache: LiveCache) -> Callable[[discord.Interaction, str], Coroutine[None, None, list[slash.Choice[int]]]]:

    async def load_cache(interaction: discord.Interaction, current: str) -> list[slash.Choice[int]]:
        return [
            slash.Choice(name=playlist[1], value=playlist[0])
            for playlist in cache(interaction, current)
        ]
    
    return load_cache



class MNewPlaylist(discord.ui.Modal, title="Create a Playlist"):
    
    name = TextInput(label="Playlist Title", placeholder="Title", required=False, min_length=2, max_length=20)
    url = TextInput(label="External Url", placeholder="http://", required=False, min_length=29)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.name is None and self.url is None:
            modal = self
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.stop()
            return

        await interaction.response.defer()

        if self.url.value:
            if (url := yarl.URL(self.url.value)).host is None:
                await interaction.followup.send("This url is not supported.")
                return
            
            if 'yout' in url.host: # type: ignore
                playlist = YouTubePlaylist.get(interaction, str(url))
            elif 'spotify' in url.host: # type: ignore
                playlist = SpotifyPlaylist.get(interaction, str(url))
            else:
                await interaction.followup.send("This url is not supported.")
                return
        else:
            if LocalPlaylist.exists(interaction, str(self.name)):
                await interaction.followup.send("This playlist already exists!", ephemeral=True)
                return
            playlist = LocalPlaylist.create(str(self.name), interaction, PermissionLevel.Viewable)

        await playlist.dump(interaction)
        await interaction.followup.send(f"Playlist `{playlist.title}` created.")

        self.stop()



class Playlists(slash.Group):


    @slash.command(name="new", description="Creates a playlist.")
    async def new_playlist(self, interaction: discord.Interaction) -> None:
        modal = MNewPlaylist()
        await interaction.response.send_modal(modal)


    @slash.command(name='owner', description='Take action on a playlist owner.')
    @slash.describe(permission_level='Ownership level ranges from 1 (disown) to 5 (admin). For a complete info message run /playlist ownership')
    @slash.autocomplete(playlist=autocomplete(Cached.playlists))
    async def owner_actions(self, interaction: discord.Interaction, playlist: int, user: discord.Member, permission_level: slash.Range[int, 1, 5], ephemeral: bool = False) -> None:
        _playlist = await LocalPlaylist.load(interaction, playlist)
        await _playlist.set_owner(user, PermissionLevel(permission_level-1))
        if permission_level == 1:
            message = f'{user.mention} has been removed from owners of playlist `{_playlist.title}`'
        else:
            message = f'{user.mention} has been granted permission level {permission_level} for playlist {_playlist.title}'
        await interaction.response.send_message(f'Done! {message}!', ephemeral=ephemeral)


    @slash.command(name='ownership', description='Describes how playlists are managed by owners.')
    async def ownership_info(self, interaction: discord.Interaction) -> None:
        MESSAGE = (
            "There are 5 levels of ownership of a playlist:" +
            "\n> 1. The user cannot perform any action on a playlist, nor even see the playlist if private." +
            "\n> 2. The user can see the playlist, but cannot perform any action." +
            "\n> 3. The user can add songs to the playlist (but cannot remove them)." +
            "\n> 4. The user can add and remove songs to the playlist." +
            "\n> 5. The user is considered an admin and can manage songs in the playlist, as well as rename and delete the playlist." +
            "\n\nAdditionally, playlist can have a privacy level, that overrides any user privacy level, e. g. if a playlist's privacy level is 2 anyone can see it, even if their ownership level is 1."
        )
        await interaction.response.send_message(MESSAGE)


    @slash.command(name="show", description="Shows a playlist. If the playlist is private it will be sent as a private message.")
    @slash.autocomplete(name=autocomplete(Cached.playlists))
    async def show_playlist(self, interaction: discord.Interaction, name: int) -> None: # NOTE: name is actually playlist_id
        await interaction.response.defer()

        playlist = await LocalPlaylist.load(interaction, name) 

        pView = ui.PlaylistPaginator(playlist)
        await interaction.followup.send(embed=playlist.embeds()[0], view=pView) 


    @slash.command(name="by", description="Sends an embed with all of your playlists (even if private).")
    async def show_all_playlists(self, interaction: discord.Interaction, person: discord.User | None = None) -> None:
        await interaction.response.defer()

        author = person or interaction.user
        lister = UserLister.load(author, interaction.guild is None and person is None)
        embeds = lister.embeds()

        await interaction.followup.send(embed=embeds[0], view=ui.MenuView(embeds))

    
    @slash.command(name='here', description='Shows all the playlist of this server.')
    @slash.guild_only
    async def show_here(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        lister = GuildLister.load(interaction.guild) # type: ignore[non-null]
        embeds = lister.embeds()

        await interaction.followup.send(embed=embeds[0], view=ui.MenuView(embeds))



class Advices(slash.Group):


    @slash.command(name='show', description='Shows your adviced songs.')
    async def show_advices(self, interaction: discord.Interaction) -> None:
        advices = await LocalPlaylist.load(interaction, title='Advices', target_id=interaction.user.id)
        await interaction.response.send_message(embed=advices.embeds()[0], view=ui.MenuView(advices.embeds()))


    @slash.command(name='random', description='Sends a random song from your adviced songs.')
    async def random_advice(self, interaction: discord.Interaction) -> None:
        advices = await LocalPlaylist.load(interaction, title='Advices', target_id=interaction.user.id)
        await interaction.response.send_message(embed=random.choice(advices).embed) # TODO: Add context and maybe change embed


    @slash.command(name='give', description='Advice a song to someone.')
    async def give_advice(self, interaction: discord.Interaction, song: str, to: discord.Member, mention: bool = True) -> None:
        await interaction.response.defer()
        advices = await LocalPlaylist.load(interaction, title='Advices', target_id=to.id)
        if not song.startswith("http"):
            choice = SongsChoice.search(song, SpotifySong)
            _song = await choice.choose(interaction)
        else:
            _song = await SpotifySong.find(song)

        if _song not in advices:
            await advices.add_song(_song, interaction.user.id)
            if mention:
                message = f"Adviced to {to.mention}"
            else:
                message = f"Adviced to {to.display_name}"
        else:
            message = f"This song is already in {to.display_name}'s advice list"

        await interaction.followup.send(message, embed=_song.embed)


    @slash.command(name='remove', description='Remove a song from your adviced songs.')
    @slash.autocomplete(song=autocomplete(Cached.advices))
    async def remove_advice(self, interaction: discord.Interaction, song: int) -> None:
        _song = LocalSong.load(song)
        advices = await LocalPlaylist.load(interaction, title='Advices', target_id=interaction.user.id)

        advices.remove_song(_song)
        await interaction.response.send_message(f'Done! {_song.title} removed from your advices!')


class Favourites(slash.Group):

    @slash.command(name='show', description='Shows your favourites songs.')
    async def show_songs(self, interaction: discord.Interaction) -> None:
        liked_songs = await LocalPlaylist.load(interaction, title='Liked', target_id=interaction.user.id)
        await interaction.response.send_message(embed=liked_songs.embeds()[0], view=ui.MenuView(liked_songs.embeds()))

    @slash.command(name='add', description='Adds a song to your favourites.')
    async def add_song(self, interaction: discord.Interaction, song: str) -> None:
        await interaction.response.defer()
        favourites = await LocalPlaylist.load(interaction, title='Liked', target_id=interaction.user.id)
        if not song.startswith("http"):
            choice = SongsChoice.search(song, SpotifySong)
            _song = await choice.choose(interaction)
        else:
            _song = await SpotifySong.find(song)

        if _song not in favourites:
            await favourites.add_song(_song, interaction.user.id)
            message = f"{_song.title} added to your favourites!"
        else:
            message = f"This song already is in favourites list."

        await interaction.followup.send(message, embed=_song.embed)

    @slash.command(name='remove', description='Removes a song from your favourites.')
    @slash.autocomplete(song=autocomplete(Cached.favourites))
    async def remove_song(self, interaction: discord.Interaction, song: int) -> None:
        _song = LocalSong.load(song)
        favourites = await LocalPlaylist.load(interaction, title='Liked', target_id=interaction.user.id)

        favourites.remove_song(_song)
        await interaction.response.send_message(f'Done! {_song.title} removed from your favourites!')