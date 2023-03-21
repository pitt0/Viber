from typing import Literal, NotRequired
from typing import TypedDict



class Thumbnail(TypedDict):
    url: str
    height: NotRequired[int]
    width: NotRequired[int]
    preference: int
    id: str
    resolution: NotRequired[str]

class Result(TypedDict):
    id: str
    title: str
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
    webpage_url: str
    categories: list[str]
    tags: list[str]
    release_timestamp: int | None
    channel: str
    channel_follower_count: int
    original_url: str
    fulltitle: str
    playlist: str | None
    playlist_index: int | None
    display_id: str
    duration_string: str
    url: str
    language: str