from dataclasses import dataclass
from enum import Enum, auto
from typing_extensions import Self

import discord

from .utils import (
    BadRequest,
    NotFound,
    WrongLink
)

from .utils import genius

from .utils import spotify as sp
from .utils import youtube as yt

from .base.info import *
from .base.song import Song as MetaSong

from ui.songs import VChoosableSong


__all__ = (
    "AdviceableSong",
    "ChoosableSong",
    "PlayableSong",

    "search",
    "choose",
    "Purpose"
)


class Purpose(Enum):
    Advice = auto()
    Play = auto()
    Playlist = auto()
    Lyrics = auto()


def fetch_song(reference: str, purpose: Purpose) -> MetaSong:
    match purpose:
        case Purpose.Play | Purpose.Lyrics:
            song_type = PlayableSong
        case Purpose.Playlist:
            song_type = PlaylistSong
        case Purpose.Advice:
            song_type = AdviceableSong
        case _:
            raise ValueError()
         
    if not reference.startswith("http"):
        return song_type.from_reference(reference)

    elif "open.spotify.com" in reference:
        song = song_type.from_spotify(reference)
        if song is None:
            raise WrongLink(f"(This link)[{reference}] returned no result.")
        
        return song
    
    elif "youtu.be" in reference or "youtube.com" in reference:
        return song_type.from_youtube(reference)
    
    raise BadRequest(f"(This type of links)[{reference}] are not supported.")
    

def search(purpose: Purpose, reference: str) -> MetaSong:
    song = fetch_song(reference, purpose)
    song.cache(reference)
    return song

async def choose(interaction: discord.Interaction, purpose: Purpose, reference: str) -> MetaSong:
    songs = ChoosableSong.from_reference(reference)
    if len(songs) == 0:
        raise NotFound(f"Searching `{reference}` returned no result.")
    song = songs[0]
    
    if len(songs) > 1:
        view = VChoosableSong(songs)
        if interaction.response.is_done():
            await interaction.followup.send(embed=song.embed, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(embed=song.embed, view=view, ephemeral=True)
        await view.wait()
        song = view.current_song

    match purpose:
        case Purpose.Advice:
            song = AdviceableSong.from_choice(song)

        case Purpose.Play | Purpose.Lyrics:
            song = PlayableSong.from_choice(song)

        case Purpose.Playlist:
            song = PlaylistSong.from_choice(song)

        case _:
            raise ValueError()

    song.cache(reference)
    return song

@dataclass
class ChoosableSong:

    id: str
    title: str
    author: str
    album: str
    thumbnail: str
    duration: str
    year: int
    url: str

    def __post_init__(self) -> None:
        embed = discord.Embed(
            color=discord.Color.dark_purple(),
            title=self.title,
            description=f"{self.author} • {self.album}",
            url=self.url
        )
        embed.set_thumbnail(url=self.thumbnail)
        embed.add_field(name="Year", value=self.year)
        embed.add_field(name="Duration", value=self.duration)

        self.embed = embed

    @classmethod
    def from_reference(cls, reference: str) -> list[Self]:
        songs = []
        info = sp.search(reference)
        if len(info["tracks"]["items"]) > 0:
            tracks = info["tracks"]["items"]
            for track in tracks:
                info = SpotifyInfo(choosable=True, **track)
                songs.append(cls(**info))
        else:
            results = yt.search_infos(reference)
            for result in results:
                info = YTInfo(choosable=True, **result)
                songs.append(cls(**info))
        return songs


@dataclass
class AdviceableSong(MetaSong):

    def __post_init__(self) -> None:
        super().__post_init__()

        embed = discord.Embed(
            color=discord.Color.dark_purple(),
            title=self.title,
            description=f"{self.author} • {self.album}",
            url=self.url
        )
        embed.set_thumbnail(url=self.thumbnail)
        embed.add_field(name="Duration", value=self.duration)
        embed.add_field(name="Year", value=self.year)
        self.embed = embed


@dataclass
class PlayableSong(MetaSong):

    lyrics: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        embed = discord.Embed(
            color=discord.Color.dark_purple(),
            title=self.title,
            description=f"{self.author} • {self.album}",
            url=self.url
        )
        embed.set_thumbnail(url=self.thumbnail)
        embed.add_field(name="Duration", value=self.duration)

        self.lyrics = genius.lyrics(self)
        lyrics = discord.Embed(
            title=self.title,
            description=self.lyrics,
            color=discord.Color.dark_purple(),
            url=self.url
        ).set_thumbnail(url=self.thumbnail)

        self.embeds = [embed, lyrics]

@dataclass
class PlaylistSong(MetaSong):
    pass