from typing import Any, Literal
from typing import TypedDict


class Album(TypedDict):
    name: str
    id: str

class FeedbackToken(TypedDict):
    add: None
    remove: None

class Artist(TypedDict):
    name: str
    id: str

class Thumbnail(TypedDict):
    url: str
    width: int
    height: int


class VideoResult(TypedDict):
    category: Literal['Top result', 'Videos']
    resultType: Literal['video']
    title: str
    views: str
    videoType: Literal['MUSIC_VIDEO_TYPE_OMV', 'MUSIC_VIDEO_TYPE_UGC']
    videoId: str
    duration: str
    year: Any | None
    artists: list[Artist]
    duration_seconds: int
    thumbnails: list[Thumbnail]

class SongResult(TypedDict):
    category: Literal['Songs'] # maybe also 'Top result'
    resultType: Literal['song']
    title: str
    album: Album
    feedbackTokens: FeedbackToken
    videoId: str
    videoType: Literal['MUSIC_VIDEO_TYPE_ATV']
    duration: str
    year: None
    artists: list[Artist]
    duration_seconds: int
    isExplicit: bool
    thumbnails: list[Thumbnail]

class ArtistResult(TypedDict):
    category: Literal['Artists'] # maybe also 'Top result'
    resultType: Literal['artist']
    artist: str
    shuffleId: str
    radioId: str
    browseId: str
    thumbnails: list[Thumbnail]

class CommunityPlaylistResult(TypedDict):
    category: Literal['Community playlists'] #  maybe also 'Top result'
    resultType: Literal['playlist']
    title: str
    itemCount: str
    author: str
    browseId: str
    thumbnails: list[Thumbnail]

class AlbumResult(TypedDict):
    category: Literal['Albums'] #  maybe also 'Top result'
    resultType: Literal['album']
    title: str
    type: Literal['Album', 'Single']
    duration: None
    year: str
    artists: list[Artist]
    browseId: str
    isExplicit: bool
    thumbnails: list[Thumbnail]



Result = VideoResult | SongResult | ArtistResult | CommunityPlaylistResult | AlbumResult



class VideoDetails(TypedDict):
    videoId: str
    title: str
    lengthSeconds: str
    channelId: str
    isOwnerViewing: bool
    isCrawlable: bool
    thumbnail: dict
    allowRatings: bool
    viewCount: str
    author: str
    isLowLatencyLiveStream: bool
    isPrivate: bool
    isUnpluggedCorpus: bool
    latencyClass: str
    musicVideoType: str
    isLiveContent: bool

class SongData(TypedDict):
    playabilityStatus: dict
    streamingData: dict
    playbackTracking: dict
    videoDetails: VideoDetails
    microformat: dict

