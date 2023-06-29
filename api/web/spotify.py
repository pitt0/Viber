import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from typing import Any


load_dotenv()
auth_manager = SpotifyOAuth()
sp = spotipy.Spotify(auth_manager=auth_manager)

__all__ = (
    "search",
    "from_url"
)

def search(query: str, limit: int = 5) -> list[dict[str, Any]]:
    # NOTE: sp.search() could return None
    return (sp.search(query, limit=limit) or {"tracks": {"items": []}})["tracks"]["items"] 



def track(id: str) -> dict[str, Any]:
    return sp.track(id) # type: ignore[valid-type]

def playlist(id: str) -> dict[str, Any]:
    return sp.playlist(id) # type: ignore[valid-type]

def album(id: str) -> dict[str, Any]:
    return sp.album(id) # type: ignore[valid-type]

def artist(id: str) -> dict[str, Any]:
    return sp.artist(id) # type: ignore[valid-type]

def show(id: str) -> dict[str, Any]:
    return sp.show(id) # type: ignore[valid-type]

def from_url(url: str) -> dict[str, Any]:
    parts = url.split("/")
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