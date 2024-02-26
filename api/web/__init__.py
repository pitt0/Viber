from .spotify import SpotifyAPI as _SpotifyAPI
from .youtube import YouTubeAPI as _YouTubeAPI
from models import ExternalSong, Song
from typings import NGExternalProvider


__all__ = 'SongsAPI',


class SongsAPI:

    @staticmethod
    async def search(query: str, limit: int = 5, provider: NGExternalProvider = 'spotify') -> list[ExternalSong] | None:
        match provider:
            case 'spotify':
                return await _SpotifyAPI.search(query, limit)
            case 'youtube':
                return await _YouTubeAPI.search(query, limit)
            case 'genius':
                raise NotImplementedError
            
    @staticmethod
    async def load(url: str) -> ExternalSong | None:
        if 'open.spotify.com' in url:
            return await _SpotifyAPI.load_song(url)
        else: # TODO: we should check if it's a youtube url maybe
            return await _YouTubeAPI.load_song(url)
        
    @staticmethod
    def get_source(song: Song) -> str:
        return _YouTubeAPI.get_source(song)