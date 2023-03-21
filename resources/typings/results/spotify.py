from typing import Literal, NotRequired
from typing import TypedDict


class ArtistEntry(TypedDict):
    external_url: dict[str, str]
    href: str
    id: str
    name: str
    type: Literal['artist']
    uri: str


class AlbumImageEntry(TypedDict):
    height: int
    url: str
    width: int

class AlbumEntry(TypedDict):
    album_type: Literal['album', 'single']
    artists: list[ArtistEntry]
    available_markets: list[str]
    external_urls: dict[str, str]
    href: str
    id: str
    images: list[AlbumImageEntry]
    name: str
    release_date: str
    release_date_precision: Literal['day', 'month', 'year']
    total_tracks: int
    tracks: NotRequired['TrackEntries']
    type: Literal['album']
    uri: str


class TrackData(TypedDict):
    album: NotRequired[AlbumEntry]
    artists: list[ArtistEntry]
    available_markets: list[str]
    disc_number: int
    duration_ms: int
    explicit: bool
    external_ids: NotRequired[dict[str, str]]
    external_urls: dict[str, str]
    href: str
    id: str
    is_local: bool
    name: str
    popularity: int
    preview_url: str
    track_number: int
    type: Literal['track']
    uri: str

class TrackEntries(TypedDict):
    href: str
    items: list[TrackData]
    limit: int
    next: str
    offset: int
    previous: str
    total: int

class Result(TypedDict):
    tracks: TrackEntries