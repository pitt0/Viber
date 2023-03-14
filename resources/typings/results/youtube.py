from typing import Literal, NotRequired
from typing import TypedDict



class Format(TypedDict):
    format_id: str
    format_note: str
    ext: str
    protocol: str
    acodec: str
    vcodec: str
    url: str
    width: int
    height: int
    fragments: list
    audio_ext: str
    video_ext: str
    format: str
    resolution: str
    http_headers: dict[str, str]

class Thumbnail(TypedDict):
    url: str
    height: NotRequired[int]
    width: NotRequired[int]
    preference: int
    id: str
    resolution: NotRequired[str]

class Caption(TypedDict):
    ext: str
    url: str
    name: str

class Chapter(TypedDict):
    start_time: float
    title: str
    end_time: int

class Result(TypedDict):
    id: str
    title: str
    formats: list[Format]
    thumbnails: list[Thumbnail]
    thumbnail: str
    description: str
    upload_date: str
    uploader: str
    uploader_id: str
    uploader_url: str
    channel_id: str
    channel_url: str
    duration: int
    view_count: int
    average_rating: None
    age_limit: int
    webpage_url: str
    categories: list[str]
    tags: list[str]
    playable_in_embed: bool
    is_live: bool
    was_live: bool
    live_status: str
    release_timestamp: int | None
    automatic_captions: dict[str, list[Caption]]
    subtitles: dict
    chapters: list[Chapter] | None
    like_count: int
    channel: str
    channel_follower_count: int
    availability: str
    __post_extractor: None
    original_url: str
    webpage_url_basename: str
    webpage_url_domain: str
    extractor: str
    extractor_key: str
    fulltitle: str
    playlist: str | None
    playlist_index: int | None
    display_id: str
    duration_string: str
    requested_subtitles: None
    __has_drm: bool
    asr: int
    filesize: int
    format_id: str
    format_note: str
    source_preference: int
    fps: int | None
    height: int | None
    quality: int
    tbr: float
    url: str
    width: int | None
    language: str
    language_preference: int
    ext: str
    vcodec: str
    acodec: str
    dynamic_range: Literal['SDR'] | None
    abr: float
    downloader_options: dict[str, int]
    container: str
    protocol: str
    audio_ext: str
    video_ext: str
    format: str
    resolution: str
    http_headers: dict[str, str]