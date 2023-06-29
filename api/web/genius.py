from dotenv import load_dotenv
from lyricsgenius.genius import Genius
from typing import Any


load_dotenv()
genius = Genius()


def search(query: str) -> dict[str, Any]:
    return genius.search(query)


def remove_suffix(lyric: str) -> str:
    if lyric.endswith("Embed"):
        lyric = lyric.removesuffix("Embed")
        while lyric[-1].isnumeric():
            lyric = lyric.removesuffix(lyric[-1])
    return lyric 

def remove_prefix(lyric: str) -> str:
    if "Lyrics" not in lyric:
        return lyric
    
    words = lyric.split()
    for word in words:
        lyric = lyric.removeprefix(f"{word} ")
        if word.startswith("Lyrics"):
            lyric = word.removeprefix("Lyrics") + " " + lyric
            break
    return lyric

def lyrics(song_id: int) -> str:
    l = genius.lyrics(song_id)
    if l is None: 
        return ""
    
    l = remove_prefix(l)
    l = remove_suffix(l)
    return l