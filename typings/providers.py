from typing import Literal

type Local = Literal['local']
type Spotify = Literal['spotify']
type YouTube = Literal['youtube']
type Genius = Literal['genius']

type Provider = Literal[Local, Spotify, YouTube, Genius]
type ExternalProvider = Literal[Spotify, YouTube, Genius]
type NGProvider = Literal[Local, Spotify, YouTube]
type NGExternalProvider = Literal[Spotify, YouTube]

type DataID = tuple[str, int | None, str | None, str | None]

type ExternalID = str | int
type NGExternalID = str
type LocalID = str
