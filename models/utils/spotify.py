from typing import Any
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from dotenv import load_dotenv


load_dotenv()
auth_manager = SpotifyOAuth()
sp = spotipy.Spotify(auth_manager=auth_manager)

__all__ = (
    'search',
)

def search(song: str) -> dict[str, Any]:
    return sp.search(song, limit=5)



def track(id: str) -> dict[str, Any]:
    return sp.track(id)

def playlist(id: str) -> dict[str, Any]:
    return sp.playlist(id)

def album(id: str) -> dict[str, Any]:
    return sp.album(id)

def artist(id: str) -> dict[str, Any]:
    return sp.artist(id)

def show(id: str) -> dict[str, Any]:
    return sp.show(id)

def from_link(link: str) -> dict[str, Any]:
    parts = link.split('/')
    check = parts[-2]
    id = parts[-1].split('?si')[0]
    match check:
        case 'track':
            return track(id)
        
        case 'playlist':
            return playlist(id)
        
        case 'album':
            return album(id)
        
        case 'artist':
            return artist(id)
        
        case 'show':
            return show(id)
        
        case _:
            return {}