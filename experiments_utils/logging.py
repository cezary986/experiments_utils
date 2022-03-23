import logging
import os
import shutil
from . import settings

logging_levels = [
    ('DEBUG', logging.DEBUG),
    ('INFO', logging.INFO),
    ('WARN', logging.WARN),
    ('ERROR', logging.ERROR),
]


def configure_logging(_file_, run_log_dir: str, dir_path: str):
    if settings.EXPERIMENT_BASE_LOGGING_DIR is None:
        settings.EXPERIMENT_BASE_LOGGING_DIR = f'{dir_path}/logs/{run_log_dir}'
        print(
            f'Logs directory not configured, use default logs dir: "{settings.EXPERIMENT_BASE_LOGGING_DIR}"')
    else:
        if settings.EXPERIMENT_BASE_LOGGING_DIR[-1] != '/':
            settings.EXPERIMENT_BASE_LOGGING_DIR = f'{settings.EXPERIMENT_BASE_LOGGING_DIR}/'
        print(
            f'Use configured directory for logs: "{settings.EXPERIMENT_BASE_LOGGING_DIR}"')
    os.makedirs(settings.EXPERIMENT_BASE_LOGGING_DIR, exist_ok=True)

def get_step_logger(name: str, config_key: str) -> logging.Logger:
    log_file_path = f'{settings.EXPERIMENT_BASE_LOGGING_DIR}/{config_key}/{name}'
    os.makedirs(log_file_path, exist_ok=True)
    log_file_path = f'{log_file_path}/{name}'
    logger = logging.getLogger(f'{name}.{config_key}')
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages

    for level_name, level in logging_levels:
        fh = logging.FileHandler(f'{log_file_path}.{level_name}.log')
        formatter = logging.Formatter(
            '[%(levelname)s] %(asctime)s %(message)s')
        fh.setFormatter(formatter)
        fh.setLevel(level)
        logger.addHandler(fh)

    return logger


def get_experiment_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    log_file_path = f'{settings.EXPERIMENT_BASE_LOGGING_DIR}/log'

    for level_name, level in logging_levels:
        fh = logging.FileHandler(f'{log_file_path}.{level_name}.log')
        formatter = logging.Formatter(
            '[%(levelname)s] %(asctime)s %(message)s')
        fh.setFormatter(formatter)
        fh.setLevel(level)
        logger.addHandler(fh)

    logger.addHandler(fh)
    return logger


def clear_logs():
    log_directory_path = f'{os.path.dirname(os.path.realpath(__file__))}/../../logs'
    if os.path.exists(log_directory_path):
        shutil.rmtree(log_directory_path)
    os.makedirs(log_directory_path, exist_ok=True)

