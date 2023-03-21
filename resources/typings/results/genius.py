from typing import TypedDict



class ArtistData(TypedDict):
    id: int
    image_url: str
    name: str
    url: str


class SongResult(TypedDict):
    artist_names: str
    full_title: str
    id: int
    instrumental: bool
    language: str
    release_date_components: dict[str, int]
    release_date_with_abbreviated_month_for_display: str
    song_art_image_thumbnail_url: str
    song_art_image_url: str
    title: str
    url: str
    featured_artists: list[ArtistData]
    primary_artist: ArtistData


class SongData(TypedDict):
    highlights: list
    index: str
    type: str
    result: SongResult


class Result(TypedDict):
    hits: list[SongData]