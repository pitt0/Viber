from .errors import *

from .database import Connector

from .youtube import *
from .spotify import *

with open('resources/utils/ffmpeg.json') as f:
    FFMPEG_OPTIONS = json.load(f)