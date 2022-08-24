from typing import Any
import yt_dlp
import json
import re
import urllib.request


__all__ = (
    'from_link',
    'get_urls',
    'search_infos'
)

with open('database/options.json') as f:
    OPTS = json.load(f)

yt = yt_dlp.YoutubeDL(OPTS)

def from_link(link: str) -> dict[str, Any]:
    return yt.extract_info(link, download=False)

def get_urls(query: str) -> list[str]:
    html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={query.replace(' ', '+').encode('utf-8')}")
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    ids = []
    [ids.append(video_id) for video_id in video_ids if video_id not in ids]

    return [f"https://www.youtube.com/watch?v={video_id}" for video_id in ids[:5]]

def get_url(query: str) -> str:
    html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={query.replace(' ', '+').encode('utf-8')}")
    video_id = re.findall(r"watch\?v=(\S{11})", html.read().decode())[0]
    return f"https://www.youtube.com/watch?v={video_id}"

def search_infos(query: str) -> list[dict[str, Any]]:

    if ' ' in query:
        query = query.replace(' ', '+')
    
    links = get_urls(query)

    infos = []
    for link in links:
        infos.append(from_link(link))

    return infos

def search_info(query: str) -> dict[str, Any]:

    if ' ' in query:
        query = query.replace(' ', '+')
    
    link = get_url(query)

    return from_link(link)