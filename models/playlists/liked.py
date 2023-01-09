import resources.connections as conn

from .base import Playlist
from models.songs import Song
from resources import USER


__all__ = ("LikedSongs",)


class LikedSongs(Playlist):

    __slots__ = "user"

    cache = conn.LikedSongsCache

    def __init__(self, user: USER, songs: list | None = None):
        super().__init__(f"{user.display_name}'s Liked Songs")
        self.user = user
        self.id = self.user.id
        self.songs = songs or []

    @classmethod
    def from_database(cls, person: USER):
        songs: list[Song] = []
        song_ids = cls.load(person)

        for song_id in song_ids:
            songs.append(Song.from_id(song_id))

        return cls(person, songs)