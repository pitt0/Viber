from yt_dlp import YoutubeDL
from ytmusicapi import YTMusic
from typing import Any, Literal

import json


__all__ = (
    "search",
    "source"
)

with open("database/options.json") as f:
    OPTS = json.load(f)

yt = YoutubeDL(OPTS)
ytm = YTMusic()


def search(query: str, filter: Literal['songs', 'artists', 'albums'], limit: int = 5) -> list[dict[str, Any]]:
    return ytm.search(query, filter, limit=limit)


def item(id: str) -> dict[str, Any]:
    return ytm.get_song(id) # type: ignore

def album(id: str) -> dict[str, Any]:
    return ytm.get_album(id) # type: ignore

def playlist(id: str) -> dict[str, Any]:
    return ytm.get_playlist(id)


def source(url: str) -> str:
    return yt.extract_info(url, download=False)['url'] # type: ignore
