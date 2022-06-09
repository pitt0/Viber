from typing import Any
import yt_dlp
import json
import re
import urllib.request


with open('database/options.json') as f:
    OPTS = json.load(f)

yt = yt_dlp.YoutubeDL(OPTS)

def search_urls(query: str) -> list[str]:
    html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={query.replace(' ', '+').encode('utf-8')}")
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())

    return [f"https://www.youtube.com/watch?v={video_id}" for video_id in video_ids[:5]]

def search(query: str) -> list[dict[str, Any]]:

    if ' ' in query:
        query = query.replace(' ', '+')
    
    links = search_urls(query)

    infos = []
    for link in links:
        infos.append(yt.extract_info(link, download=False))

    return infos

def from_link(link: str) -> dict[str, Any]:
    return yt.extract_info(link, download=False)