from yt_dlp import YoutubeDL
from ytmusicapi import YTMusic
from typing import Any, Literal
from typing import overload

import json

from resources.typings.results import ytmusic

__all__ = (
    "search",
    "source"
)

with open("database/options.json") as f:
    OPTS = json.load(f)

yt = YoutubeDL(OPTS)
ytm = YTMusic()


@overload
def search(query: str, filter: Literal['songs'], limit: int = 5) -> list[ytmusic.SongResult]:
    ...

@overload
def search(query: str, filter: Literal['artists'], limit: int = 5) -> list[ytmusic.ArtistResult]:
    ...

@overload
def search(query: str, filter: Literal['albums'], limit: int = 5) -> list[ytmusic.AlbumResult]:
    ...

def search(query: str, filter: str, limit: int = 5) -> Any:
    return ytm.search(query, filter, limit=limit)


def item(id: str) -> ytmusic.SongData:
    return ytm.get_song(id) # type: ignore

def album(id: str) -> ytmusic.AlbumDetails:
    return ytm.get_album(id) # type: ignore

def playlist(id: str) -> dict[str, Any]:
    return ytm.get_playlist(id)


def source(url: str) -> str:
    return yt.extract_info(url, download=False)['url'] # type: ignore
