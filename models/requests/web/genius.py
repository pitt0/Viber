from dotenv import load_dotenv
from lyricsgenius.genius import Genius

from resources.typings import genius as gl

load_dotenv()
genius = Genius()


def search(query: str) -> gl.Result:
    return genius.search(query)


def removesuffix(lyric: str) -> str:
    if lyric.endswith("Embed"):
        lyric = lyric.removesuffix("Embed")
        while lyric[-1].isnumeric():
            lyric = lyric.removesuffix(lyric[-1])
    return lyric 

def removeprefix(lyric: str) -> str:
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
    
    l = removeprefix(l)
    l = removesuffix(l)
    return l