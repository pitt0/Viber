import json

from .errors import *

from .genius import *
from .spotify import *
from .youtube import *

from .typing import *

with open("database/ffmpeg.json") as f:
    FFMPEG_OPTIONS = json.load(f)