from typing import NotRequired
from typing import TypedDict



class ArtistData(TypedDict):
    _type: str
    api_path: str
    header_image_url: str
    id: int
    image_url: str
    index_character: str
    is_meme_verified: bool
    is_verified: bool
    name: str
    slug: str
    url: str
    iq: NotRequired[int]

class SongStatsData(TypedDict):
    unreviewed_annotations: int
    hot: bool
    pageviews: NotRequired[int]


class SongResult(TypedDict):
    _type: str
    annotation_count: int
    api_path: str
    artist_names: str
    full_title: str
    header_image_thumbnail_url: str
    header_image_url: str
    id: int
    instrumental: bool
    language: str
    lyrics_owner_id: int
    lyrics_state: str
    lyrics_updated_at: int
    path: str
    pyongs_count: int
    relationships_index_url: str
    release_date_components: dict[str, int]
    release_date_for_display: str
    release_date_with_abbreviated_month_for_display: str
    song_art_image_thumbnail_url: str
    song_art_image_url: str
    stats: SongStatsData
    title: str
    title_with_featured: str
    updated_by_human_at: int
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