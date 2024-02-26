import discord
from .base import *
from .external import *
from collections.abc import Sequence
from functools import cached_property
from typings import ExternalProvider, ExternalID



__all__ = (
    'Track',
    'Album',
    'Artist',

    'ExternalTrack',
    'ExternalAlbum',
    'ExternalArtist',

    'ExternalData',

    'Song',
    'ExternalSong',
    'LocalSong'
)


class Song[T: Track, A: Album, AR: Artist]:

    def __init__(self, track: T, album: A, authors: Sequence[AR], provider: ExternalProvider) -> None:
        self._track = track
        self.album = album
        self.authors = authors

        self._provider = provider

    def __str__(self) -> str:
        return f'{self._track.title} by {self.authors[0]}'
    
    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Song): return False
        if self._provider != __o._provider:
            return self.id == __o.id
        return (self.id == __o.external_id or self.external_id == __o.id)
    
    @cached_property
    def id(self) -> str:
        return self._track.id
    
    @cached_property
    def external_id(self) -> ExternalID | None:
        return self._track.external_id
    
    @cached_property
    def title(self) -> str:
        return self._track.title
    
    @cached_property
    def author(self) -> AR:
        return self.authors[0]

    @cached_property
    def artists(self) -> str:
        return ', '.join(artist.href for artist in self.authors)
    
    @cached_property
    def release_date(self) -> str:
        return self.album.release_date
    
    @cached_property
    def thumbnail(self) -> str:
        return self.album.thumbnail

    @cached_property
    def embed(self) -> discord.Embed:
        return discord.Embed(
            title=self._track.title,
            description=self.artists,
            colour=discord.Colour.dark_purple()
        ).set_thumbnail(url=self.thumbnail)

    @cached_property
    def lyrics(self) -> discord.Embed:
        song = gl.search(str(self))['hits'][0]['result']
        return discord.Embed(
            title=self._track.title,
            description=gl.lyrics(song['id']),
            colour=discord.Colour.dark_purple()
        )


type ExternalSong = Song[ExternalTrack, ExternalAlbum, ExternalArtist]
type LocalSong = Song[Track, Album, Artist]
