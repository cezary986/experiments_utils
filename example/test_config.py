
import _
from typing import Dict
import experiments_utils.settings as settings

settings.REMOTE_LOGGING_URL = 'http://127.0.0.1:8000'
settings.REMOTE_LOGGING_CREDENTIALS = (
    'cezary',
    'password'
)


EXPERIMENT_NAME: str = 'test_experiment'

CONFIGURATIONS: Dict[str, dict] = {
    '1': {
        'a': 0,
        'b': 2,
    },
    '2': {
        'a': 10,
        'b': 2,
    },
    '3': {
        'a': 1,
        'b': 2,
    },
    '4': {
        'a': 1,
        'b': 2
    },
    '5': {
        'a': None,
        'b': 2
    },
    '6': {
        'a': 1,
        'b': 2
    },
    '7': {
        'a': 1,
        'b': 2,
    }
}
