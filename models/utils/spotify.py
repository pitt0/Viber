from typing import Any
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from dotenv import load_dotenv


load_dotenv()
auth_manager = SpotifyOAuth()
sp = spotipy.Spotify(auth_manager=auth_manager)

__all__ = (
    "search",
    "from_link"
)

def search(song: str, limit: int = 5) -> list[dict[str, Any]]:
    return (sp.search(song, limit=limit) or {"tracks": {"items": []}})["tracks"]["items"] 



def track(id: str) -> dict[str, Any]:
    return sp.track(id) or {}

def playlist(id: str) -> dict[str, Any]:
    return sp.playlist(id) or {}

def album(id: str) -> dict[str, Any]:
    return sp.album(id) or {}

def artist(id: str) -> dict[str, Any]:
    return sp.artist(id) or {}

def show(id: str) -> dict[str, Any]:
    return sp.show(id) or {}

def from_link(link: str) -> dict[str, Any]:
    parts = link.split("/")
    check = parts[-2]
    id = parts[-1].split("?si")[0]
    match check:
        case "track":
            return track(id)
        
        case "playlist":
            return playlist(id)
        
        case "album":
            return album(id)
        
        case "artist":
            return artist(id)
        
        case "show":
            return show(id)
        
        case _:
            return {}