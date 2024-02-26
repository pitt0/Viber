from typing import Any

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

from models.songs import *
from resources import Time

__all__ = ("SpotifyAPI",)


load_dotenv()
auth_manager = SpotifyOAuth()
sp = spotipy.Spotify(auth_manager=auth_manager)


class SpotifyAPI:

    @staticmethod
    def _create_track(data: dict[str, Any], query: str | None = None) -> ExternalTrack:
        return ExternalTrack(
            data["id"],
            data["name"],
            Time.from_ms(data["duration_ms"]),
            "spotify",
            query,
        )

    @staticmethod
    def _create_album(data: dict[str, Any]) -> ExternalAlbum:
        return ExternalAlbum(
            data["id"],
            data["name"],
            data["images"][0]["url"],
            data["release_date"],
            "spotify",
        )

    @staticmethod
    def _create_artist(data: dict[str, Any]) -> ExternalArtist:
        return ExternalArtist(data["id"], data["name"], "spotify")

    @classmethod
    async def search(cls, query: str, limit: int = 5) -> list[ExternalSong] | None:
        data = sp.search(query, limit=limit, type="track")

        if data is None:
            return None

        songs = []
        for track_data in data["tracks"]["items"]:
            # print(track_data)
            track = cls._create_track(track_data, query)
            album = cls._create_album(track_data["album"])
            artists = [cls._create_artist(artist) for artist in track_data["artists"]]

            songs.append(Song(track, album, artists, "spotify"))

        return songs

    @classmethod
    async def load(cls, url: str) -> ExternalData:
        check = url.split("/")[3]
        match check:
            case "track":
                track = sp.track(url)
                assert (
                    track is not None
                ), f"Spotify API request on track url returned None\nurl: {url}"
                return cls._create_track(track)

            case "playlist":
                return sp.playlist(url)  # TODO: Change

            case "album":
                album = sp.album(url)
                assert (
                    album is not None
                ), f"Spotify API request on album url returned None\nurl: {url}"
                return cls._create_album(album)

            case "artist":
                artist = sp.artist(url)
                assert (
                    artist is not None
                ), f"Spotify API request on artist url returned None\nurl: {url}"
                return cls._create_artist(artist)

        raise ValueError(f"Wrong spotify url given.\nurl: {url}")

    @classmethod
    async def load_song(cls, url: str) -> ExternalSong:
        assert url.split("/")[3] == "track"
        track = sp.track(url)
        assert (
            track is not None
        ), f"Spotify API request on track url returned None\nurl: {url}"
        return Song(
            cls._create_track(track),
            cls._create_album(track["album"]),
            [cls._create_artist(artist) for artist in track["artists"]],
            "spotify",
        )
