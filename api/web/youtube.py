import json
from time import time
from typing import Any

import yarl
from yt_dlp import YoutubeDL
from ytmusicapi import YTMusic

from models.songs import *

__all__ = ("YouTubeAPI",)


with open("settings/youtube.json") as f:
    OPTS = json.load(f)

yt = YoutubeDL(OPTS)
ytm = YTMusic()


class YouTubeAPI:

    @staticmethod
    def _create_track(data: dict[str, Any], query: str | None = None) -> ExternalTrack:
        return ExternalTrack(
            data["videoId"], data["title"], data["duration"], "youtube", query
        )

    @staticmethod
    def _create_album(data: dict[str, Any]) -> ExternalAlbum:
        return ExternalAlbum(
            data["audioPlaylistId"],
            data["title"],
            data["thumbnails"][0]["url"],
            data["year"],
            "youtube",
        )

    @staticmethod
    def _create_artist(data: dict[str, Any]) -> ExternalArtist:
        return ExternalArtist(data["id"], data["name"], "youtube")

    @staticmethod
    def raw_search(query: str, type: str, limit: int) -> list[dict[str, Any]]:
        return ytm.search(query, type, limit=limit)

    @classmethod
    async def search(cls, query: str, limit: int) -> list[ExternalSong] | None:
        data = ytm.search(query, "songs")

        if not data:
            return None

        songs: list[ExternalSong] = []
        for i, track_data in enumerate(data):
            if i == limit:
                break
            if track_data is None:
                print(f"yt track data is none for query: {query}")
                return
            if track_data["album"] is None:
                print(f"yt album data is none for query: {query}")
                return

            songs.append(
                Song(
                    cls._create_track(track_data, query),
                    cls._create_album(ytm.get_album(track_data["album"]["id"])),
                    [cls._create_artist(artist) for artist in track_data["artists"]],
                    "youtube",
                )
            )

        return songs

    @classmethod
    async def load(cls, url: str) -> ExternalData:
        # NOTE: Users-uploaded urls ['www.youtube.com' | 'youtu.be'] will 100% be videos / playlists
        # no point on checking albums / artists

        _url = yarl.URL(url)
        if _url.host != "music.youtube.com":
            # Just videos / playlists
            # TODO: playlists
            match _url.host:
                case "www.youtube.com":
                    track_data = ytm.get_song(_url.query["v"])
                case "youtu.be":
                    track_data = ytm.get_song(_url.name)
                case _:
                    raise ValueError(f"Unsupported YouTube url: {url}")

            return cls._create_track(track_data)

        match _url.parts[1]:
            case "channel":
                return cls._create_artist(ytm.get_artist(_url.parts[2]))
            case "playlist":  # either album or actual playlist
                return cls._create_album(
                    ytm.get_album(_url.query["list"])
                )  # NOTE: if this is a playlist, it should be get_playlist
            case "watch":
                return cls._create_track(ytm.get_song(_url.query["v"]))

        raise ValueError(f"{url} returned no result.")

    @classmethod
    async def load_song(cls, url: str) -> ExternalSong:
        # NOTE: not all the music videos have an album
        # TODO: fix [maybe get track data (name, author) and do a search with these keywords]
        # TODO: could also add a flag in commands like `video: bool` and if it is a video, skip all the process and just play the audio
        if "youtu.be" in url:
            try:
                track_data = ytm.get_song(url.split("/")[-1])
                track = cls._create_track(track_data)
            except KeyError:
                raise ValueError  # TODO: obv replace with a custom error
            return Song(
                track,
                cls._create_album(ytm.get_album(track_data["album"]["id"])),
                [
                    cls._create_artist(artist)
                    for artist in [
                        ytm.get_artist(ad["id"]) for ad in track_data["artists"]
                    ]
                ],
                "youtube",
            )

        assert (_url := yarl.URL(url)).parts[1] == "watch" or _url
        track_data = ytm.get_song(_url.query["v"])
        return Song(
            cls._create_track(track_data),
            cls._create_album(track_data["album"]["id"]),
            [
                cls._create_artist(artist)
                for artist in [ytm.get_artist(ad["id"]) for ad in track_data["artists"]]
            ],
            "youtube",
        )

    @classmethod
    def get_source(cls, song: Song) -> str:
        if song._provider == "youtube":
            return yt.extract_info(f"https://youtu.be/{song.external_id}", download=False)["url"]  # type: ignore[non-null]

        print(f"Fetching source url of {song}")  # NOTE: Log
        song_data = cls.raw_search(f"{song.author.name} {song.title}", "songs", 1)[0]
        if not song_data:
            raise ValueError
        return yt.extract_info(f"https://www.youtube.com/watch?v={song_data['videoId']}", download=False)["url"]  # type: ignore[non-null]
