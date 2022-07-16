import json


from .errors import *

from .spotify import *
from .youtube import *

with open('database/ffmpeg.json') as f:
    FFMPEG_OPTIONS = json.load(f)