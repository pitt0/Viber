import resources.connections as conn

from .base import Playlist
from models.songs import Song
from resources import USER

__all__ = ("Advices",)

class Advices(Playlist):

    __slots__ = "user"

    cache = conn.AdvicesCache
    
    def __init__(self, user: USER, songs):
        super().__init__(f"{user.display_name}'s Advice List", songs)
        self.user = user
        self.id = self.user.id

    @classmethod
    def from_database(cls, person: USER):
        song_ids = cls.load(person)
        songs = [Song.from_id(song_id) for song_id in song_ids]
        return cls(person, songs)