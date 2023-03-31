from typing import Self

from .base import Artist, Album, Track
from resources import LocalAlbumRequest, SongRequest

        

class LocalAlbum(Album):

    @classmethod
    def load(cls, id: int) -> Self:
        artists = []
        data = LocalAlbumRequest.get(id)
        for _, _, name, _, _, _, arts_id in data:
            artists.append(Artist(arts_id, name, f'https://open.spotify.com/artist/{arts_id}'))
        id, name, _, rd, thumbnail, sp_id, _ = data[0]
        return cls(id, name, artists, thumbnail, rd, f'https://open.spotify.com/album/{sp_id}')



class LocalSong(Track):

    @classmethod
    def load(cls, title: str) -> Self:
        artists = []
        data = SongRequest.get(title)

        for _, _, _, name, _, _, id in data:
            artists.append(Artist(id, name, f'https://open.spotify.com/artist/{id}'))
            
        id, title, album_id, _, duration, sp_id, _ = data[0]
        album = LocalAlbum.load(album_id)
        return cls(id, title, artists, album, duration, f'https://open.spotify.com/track/{sp_id}')
