from dotenv import load_dotenv
from lyricsgenius.genius import Genius

load_dotenv()
genius = Genius()

def lyrics(song) -> str:
    song_data = genius.search_song(song.data.title, song.data.author)
    if song_data is None: return "Could not find anything :("
    song_lyrics = genius.lyrics(song_data.id)
    return song_lyrics[:-5] if song_lyrics else ""

