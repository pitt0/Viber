from functools import cached_property

from typings import ExternalID, ExternalProvider

__all__ = ("Album", "Artist", "Track")


SPOTIFY_PREFIX = "https://open.spotify.com"
YOUTUBE_PREFIX = "https://music.youtube.com"


class _Data:

    external_id: ExternalID | None
    _provider: ExternalProvider

    def __init__(
        self, external_id: ExternalID | None, provider: ExternalProvider
    ) -> None:
        self.external_id = external_id
        self._provider = provider


class Artist(_Data):

    def __init__(
        self, name: str, external_id: ExternalID | None, _ext_provider: ExternalProvider
    ) -> None:
        super().__init__(external_id, _ext_provider)
        self.name = name

    @cached_property
    def url(self) -> str | None:
        match self._provider:
            case "youtube":
                return f"{YOUTUBE_PREFIX}/channel/{self.external_id}"
            case "spotify":
                return f"{SPOTIFY_PREFIX}/artist/{self.external_id}"
        return None

    def __str__(self) -> str:
        return self.name

    @cached_property
    def href(self) -> str:
        return f"[{self.name}]({self.url})" if self.url else self.name


class Album(_Data):

    def __init__(
        self,
        name: str,
        thumbnail: str,
        release_date: str,
        external_id: ExternalID,
        _ext_provider: ExternalProvider,
    ) -> None:
        super().__init__(external_id, _ext_provider)
        self.name = name
        self.thumbnail = thumbnail
        self.release_date = release_date

    @cached_property
    def url(self) -> str | None:
        match self._provider:
            case "youtube":
                return None  # f'https://music.youtube.com/???{self.external_id}'
            case "spotify":
                return f"{SPOTIFY_PREFIX}/album/{self.external_id}"
        return None


class Track(_Data):

    def __init__(
        self,
        id: str,
        title: str,
        duration: str,
        external_id: ExternalID,
        _ext_provider: ExternalProvider,
    ) -> None:
        super().__init__(external_id, _ext_provider)
        self._id = id
        self.title = title
        self.duration = duration

    @cached_property
    def url(self) -> str | None:
        match self._provider:
            case "youtube":
                return f"{YOUTUBE_PREFIX}/watch?v={self.external_id}"
            case "spotify":
                return f"{SPOTIFY_PREFIX}/track/{self.external_id}"
        return None
