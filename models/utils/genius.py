from dotenv import load_dotenv
from lyricsgenius.genius import Genius

load_dotenv()
genius = Genius()

def lyrics(song) -> str:
    song_data = genius.search_song(song.title, song.author)
    if song_data is None: return 'Could not find anything :('
    song_lyrics = genius.lyrics(song_data.id)
    return song_lyrics[:-6] if song_lyrics else ''

def d_lyrics(title, author) -> str:
    song_data = genius.search_song(title, author)
    song_lyrics = genius.lyrics(song_data.id)
    return song_lyrics[:-6] if song_lyrics else ''
