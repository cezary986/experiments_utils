from typing import Tuple
import pytz
dir_path: str = None

# Default timezone
EXPERIMENT_TIMEZONE: str = pytz.timezone('Europe/Warsaw')

EXPERIMENT_BASE_LOGGING_DIR: str = None

THREADS_LIMIT: int = 8

REMOTE_LOGGING_ENABLED: bool = False
REMOTE_LOGGING_THROTTLE: int = 10 # secons
REMOTE_LOGGING_URL: str = None
REMOTE_LOGGING_CREDENTIALS: Tuple[str, str] = None
