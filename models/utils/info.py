from . import youtube as yt

from connections import Connector


__all__ = (
    'SpotifyInfo',
    'YTInfo',
    'DataInfo'
)

def duration_string(ms: int) -> str:
    duration = ms//1000
    mins = duration//60
    secs = duration - mins * 60
    if secs < 10:
        secs = f"0{secs}"
    return f"{mins}:{secs}"

class SpotifyInfo(dict):
    def __init__(self, **kwargs) -> None:
        title = kwargs['name']
        author = kwargs['artists'][0]['name']
        
        yt_data = yt.search_info(f'{title} {author}')
        youtube = yt_data['original_url']
        source = yt_data['url']

        duration = duration_string(kwargs['duration_ms'])
                
        _dict = {
            'id': kwargs['id'],
            'title': title,
            'author': author,
            'album': kwargs['album']['name'],
            'thumbnail': kwargs['album']['images'][0]['url'],
            'duration': duration,
            'year': int(kwargs['album']['release_date'][:4]),
            'spotify': kwargs['external_urls']['spotify'],
            'youtube': youtube,
            'source': source
            }
        super().__init__(_dict)

class YTInfo(dict):
    def __init__(self, **kwargs) -> None:
        _dict = {
            'id': kwargs['id'],
            'title': kwargs['title'],
            'author': kwargs['uploader'],
            'album': kwargs.get('album', '\u200b'),
            'thumbnail': kwargs['thumbnail'],
            'duration': kwargs['duration_string'],
            'year': kwargs['upload_date'][:4],
            'youtube': kwargs['original_url'],
            'source': kwargs['url']
        }
        super().__init__(_dict)

class DataInfo(dict):
    def __init__(self, *args) -> None:
        youtube = args[8] or yt.get_url(args[1] + ' ' + args[2])
        source = args[9] or ''
        if not source:
            data = yt.from_link(youtube)
            source = data['url']

            with Connector() as cur:
                cur.execute("""UPDATE Songs
                SET Source=?,
                    Youtube=?
                WHERE ID=?;""",
                (source, youtube, args[0]))

        _dict = {
            'id': args[0],
            'title': args[1],
            'author': args[2],
            'album': args[3],
            'thumbnail': args[4],
            'duration': args[5],
            'year': args[6],
            'spotify': args[7],
            'youtube': youtube,
            'source': source
        }
        super().__init__(_dict)