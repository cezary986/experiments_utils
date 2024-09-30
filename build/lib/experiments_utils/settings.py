"""File containg settings. All of them could be over overwritten.
"""
from typing import Tuple
import pytz
dir_path: str = None

# Default timezone
EXPERIMENT_TIMEZONE: str = pytz.timezone('Europe/Warsaw')

EXPERIMENT_BASE_LOGGING_DIR: str = None  # default is './logs'
EXPERIMENT_CACHE_DIR: str = None  # default is './_cache'

THREADS_LIMIT: int = 8


LOGS_FORMAT = '[%(levelname)s] %(asctime)s %(message)s'

REMOTE_LOGGING_ENABLED: bool = False
REMOTE_LOGGING_THROTTLE: int = 10  # seconds
REMOTE_LOGGING_URL: str = None
REMOTE_LOGGING_CREDENTIALS: Tuple[str, str] = None
