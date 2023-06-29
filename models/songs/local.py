from .base import Artist, Album, Track
from api.local.albums import get as get_album
from api.local.songs import get as get_song
from functools import cached_property
from typing import Self

        

class LocalAlbum(Album):

    id: int

    @classmethod
    def load(cls, id: int) -> Self:
        artists = []
        data = get_album(id)
        for _, _, name, _, _, _, arts_id in data:
            artists.append(Artist(arts_id, name, f'https://open.spotify.com/artist/{arts_id}'))
        id, name, _, rd, thumbnail, sp_id, _ = data[0]
        return cls(id, name, artists, thumbnail, rd, f'https://open.spotify.com/album/{sp_id}')



class LocalSong(Track):

    id: int

    @cached_property
    def thumbnail(self) -> str:
        return self.album.thumbnail

    @classmethod
    def load(cls, rowid: int) -> Self:
        artists = []
        data = get_song(rowid)
        
        for  _, _, name, _, _, id in data:
            artists.append(Artist(id, name, f'https://open.spotify.com/artist/{id}'))
            
        title, album_id, _, duration, sp_id, _ = data[0]
        album = LocalAlbum.load(album_id)
        return cls(rowid, title, artists, album, duration, f'https://open.spotify.com/track/{sp_id}')
