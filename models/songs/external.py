from typings import NGExternalID, NGExternalProvider

from .base import Album, Artist, Track, _Data

__all__ = ("ExternalArtist", "ExternalAlbum", "ExternalTrack", "ExternalData")


class ExternalData(_Data):

    external_id: NGExternalID

    @property
    def id(self) -> NGExternalID:
        return self.external_id

    @property
    def provider(self) -> NGExternalProvider:
        return self._provider


class ExternalArtist(Artist, ExternalData):

    def __init__(self, id: str, name: str, provider: NGExternalProvider) -> None:
        super().__init__(name, id, provider)


class ExternalAlbum(Album, ExternalData):

    def __init__(
        self,
        id: str,
        name: str,
        thumbnail: str,
        release_date: str,
        provider: NGExternalProvider,
    ) -> None:
        super().__init__(name, thumbnail, release_date, id, provider)


class ExternalTrack(Track, ExternalData):

    reference: str | None

    def __init__(
        self,
        id: str,
        title: str,
        duration: str,
        provider: NGExternalProvider,
        reference: str | None = None,
    ) -> None:
        super().__init__(id, title, duration, id, provider)
        self.reference = reference
