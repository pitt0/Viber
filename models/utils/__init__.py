import json

from .typing import *

with open("database/ffmpeg.json") as f:
    FFMPEG_OPTIONS = json.load(f)