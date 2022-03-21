from typing import Dict, Tuple
import pytz

# Default timezone
EXPERIMENT_TIMEZONE: str = pytz.timezone('Europe/Warsaw')

EXPERIMENT_BASE_LOGGING_DIR: str = None

dir_path: str = None


REMOTE_LOGGING_URL: str = None
REMOTE_LOGGING_CREDENTIALS: Tuple[str, str] = None