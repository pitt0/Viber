import json

from .data import *
from .typing import *

from .playlists import *
from .songs import *
from .player import *

with open('database/ffmpeg.json') as f:
    FFMPEG_OPTIONS = json.load(f)