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

def get_ids(query: str) -> list[str]:
    query = query.replace(' ', '+')
    html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={query.replace(' ', '+').encode('utf-8')}")
    return re.findall(r"watch\?v=(\S{11})", html.read().decode())

def get_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"

def get_urls(video_ids: list[str]) -> list[str]:
    return [get_url(video_id) for video_id in video_ids]


def search_infos(query: str) -> list[dict[str, Any]]:

    video_ids = get_ids(query)
    links = get_urls([*set(video_ids)][: 5])

    infos = []
    for link in links:
        infos.append(from_link(link))

    return infos

def search_info(query: str) -> dict[str, Any]:

    video_id = get_ids(query)[0]
    link = get_url(video_id)

    return from_link(link)