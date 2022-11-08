from ..utils import youtube as yt

from connections import Connector


__all__ = (
    "SpotifyInfo",
    "YTInfo",
    "DataInfo",
    "ChoiceInfo"
)

def duration_string(ms: int) -> str:
    duration = ms//1000
    mins = duration//60
    secs = duration - mins * 60
    if secs < 10:
        secs = f"0{secs}"
    return f"{mins}:{secs}"

class SpotifyInfo(dict):
    def __init__(self, choosable: bool = False, **kwargs) -> None:
        _dict = {}

        title = kwargs["name"]
        author = kwargs["artists"][0]["name"]
        
        if not choosable:
            yt_data = yt.search_info(f"{title} {author}")
            youtube = yt_data["original_url"]
            source = yt_data["url"]
                        
            _dict["spotify"] = kwargs["external_urls"]["spotify"]
            _dict["youtube"] = youtube
            _dict["source"] = source

        else:
            _dict["url"] = kwargs["external_urls"]["spotify"]

        duration = duration_string(kwargs["duration_ms"])
        
        _dict["id"] = kwargs["id"]
        _dict["title"] = title
        _dict["author"] = author
        _dict["album"] = kwargs["album"]["name"]
        _dict["thumbnail"] = kwargs["album"]["images"][0]["url"]
        _dict["duration"] = duration
        _dict["year"] = int(kwargs["album"]["release_date"][:4])
        
        super().__init__(_dict)


class YTInfo(dict):
    def __init__(self, choosable: bool = False, **kwargs) -> None:
        _dict = {}

        if not choosable:
            _dict["youtube"] = kwargs["original_url"]
            _dict["source"] = kwargs["url"]
        else:
            _dict["url"] = kwargs["original_url"]

        _dict["id"] = kwargs["id"]
        _dict["title"] = kwargs["title"]
        _dict["author"] = kwargs["uploader"]
        _dict["album"] = kwargs.get("album", "\u200b")
        _dict["thumbnail"] = kwargs["thumbnail"]
        _dict["duration"] = kwargs["duration_string"]
        _dict["year"] = kwargs["upload_date"][:4]
        
        super().__init__(_dict)

class DataInfo(dict):
    def __init__(self, *args) -> None:
        youtube = args[8] or yt.get_url(args[1] + " " + args[2])
        source = args[9] or ""
        if not source:
            data = yt.from_link(youtube)
            source = data["url"]

            with Connector() as cur:
                cur.execute("""UPDATE Songs
                SET Source=?,
                    Youtube=?
                WHERE ID=?;""",
                (source, youtube, args[0]))

        _dict = {
            "id": args[0],
            "title": args[1],
            "author": args[2],
            "album": args[3],
            "thumbnail": args[4],
            "duration": args[5],
            "year": args[6],
            "spotify": args[7],
            "youtube": youtube,
            "source": source
        }
        super().__init__(_dict)

class ChoiceInfo(dict):
    def __init__(self, choice) -> None:
        if "spotify" in choice.url:
            spotify = choice.url
            yt_data = yt.search_info(f"{choice.title} {choice.author}")
            youtube = yt_data["original_url"]
            source = yt_data["url"]
            
        else:
            spotify = ""
            youtube = choice.url
            yt_data = yt.from_link(youtube)
            source = yt_data["url"]

        data = {
            "id": choice.id,
            "title": choice.title,
            "author": choice.author,
            "album": choice.album,
            "thumbnail": choice.thumbnail,
            "duration": choice.duration,
            "year": choice.year,
            "spotify": spotify,
            "youtube": youtube,
            "source": source
        }
        super().__init__(data)