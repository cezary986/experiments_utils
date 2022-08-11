import logging
import os
import shutil
import sys
from . import conf

logging_levels = [
    ('DEBUG', logging.DEBUG),
    ('INFO', logging.INFO),
    ('WARN', logging.WARN),
    ('ERROR', logging.ERROR),
]


def configure_logging(_file_, run_log_dir: str, dir_path: str):
    if conf.settings.EXPERIMENT_BASE_LOGGING_DIR is None:
        conf.settings.EXPERIMENT_BASE_LOGGING_DIR = f'{dir_path}/logs/{run_log_dir}'
        print(
            f'Logs directory not configured, use default logs dir: "{conf.settings.EXPERIMENT_BASE_LOGGING_DIR}"')
    else:
        if conf.settings.EXPERIMENT_BASE_LOGGING_DIR[-1] != '/':
            conf.settings.EXPERIMENT_BASE_LOGGING_DIR = f'{conf.settings.EXPERIMENT_BASE_LOGGING_DIR}/{run_log_dir}'
        print(
            f'Use configured directory for logs: "{conf.settings.EXPERIMENT_BASE_LOGGING_DIR}"')
    os.makedirs(conf.settings.EXPERIMENT_BASE_LOGGING_DIR, exist_ok=True)

def get_step_logger(name: str, config_key: str) -> logging.Logger:
    log_file_path = f'{conf.settings.EXPERIMENT_BASE_LOGGING_DIR}/{config_key}/{name}'
    os.makedirs(log_file_path, exist_ok=True)
    log_file_path = f'{log_file_path}/{name}'
    logger = logging.getLogger(f'{name}.{config_key}')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    # create file handler which logs even debug messages

    for level_name, level in logging_levels:
        fh = logging.FileHandler(f'{log_file_path}.{level_name}.log')
        formatter = logging.Formatter(conf.settings.LOGS_FORMAT)
        fh.setFormatter(formatter)
        fh.setLevel(level)
        logger.addHandler(fh)

    return logger


def configure_experiment_logger(logger: logging.Logger):
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(conf.settings.LOGS_FORMAT))
    logger.addHandler(console_handler)
    logger
    # create file handler which logs even debug messages
    log_file_path = f'{conf.settings.EXPERIMENT_BASE_LOGGING_DIR}/log'

    for level_name, level in logging_levels:
        fh = logging.FileHandler(f'{log_file_path}.{level_name}.log')
        formatter = logging.Formatter(
            '[%(levelname)s] %(asctime)s %(message)s')
        fh.setFormatter(formatter)
        fh.setLevel(level)
        logger.addHandler(fh)


def clear_logs():
    log_directory_path = f'{os.path.dirname(os.path.realpath(__file__))}/../../logs'
    if os.path.exists(log_directory_path):
        shutil.rmtree(log_directory_path)
    os.makedirs(log_directory_path, exist_ok=True)

