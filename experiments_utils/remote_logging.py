import logging
import threading
import traceback
from datetime import datetime

from . import experiment
from . import settings
from threading import Thread
import requests
import time

ExperimentConfig = None
lock: threading.Lock = threading.Lock()


class RemoteLogsHandler(logging.StreamHandler):
    """Logging handler writing logs to remote server."""

    def __init__(
        self,
        experiment_name: str,
        number_of_configs: int,
        experiment_version: str = None,
        config_name: str = None,

    ):
        """
        Args:
            experiment_name (str): name of experiment
            experiment_version (str, optional): experiment_version
            api_url (str): rest api url
        """
        global ExperimentConfig
        ExperimentConfig = experiment.ExperimentConfig
        logging.StreamHandler.__init__(self)
        self.api_url: str = settings.REMOTE_LOGGING_URL
        self.level = logging.DEBUG
        self.run_id: int = None
        self.number_of_configs: int = number_of_configs
        self.experiment_name: str = experiment_name
        self.experiment_version: str = experiment_version
        self.config_name: str = config_name
        self.logger: logging.Logger = None
        self._alive: bool = True
        self._setup_logger()

        self._fetch_run_id()
        self.messages_queue = []

        def flush_called():
            while self._alive:
                time.sleep(settings.REMOTE_LOGGING_THROTTLE)
                self.flush()
                self.logger.info('Flushed')
        self.thread = Thread(target=flush_called, daemon=True)
        self.thread.start()

    def _create_experiment(self):
        """Create experiment on server (or does nothing if already exists)."""
        url = f'{self.api_url}/api/experiments/'
        payload = {"name": self.experiment_name}
        headers = {'content-type': 'application/json'}
        try:
            response = requests.post(
                url, json=payload, headers=headers, auth=settings.REMOTE_LOGGING_CREDENTIALS)

            if response.status_code != 200 or (response.status_code == 400 and ('already exists' in response.text)):
                return
            else:
                self.logger.error(
                    f'Failed to create new experiment on remote server "{self.api_url}". Server returned {response.status_code} status code and following error:')
                self.logger.error(response.text)
        except Exception as error:
            self.logger.error(
                f'Failed to create new experiment on remote server "{self.api_url}" with following exception:')
            self.logger.error(str(error))
            self.logger.error(traceback.format_exc())

    def _fetch_run_id(self):
        """Save log entry to server."""
        self._create_experiment()
        url = f'{self.api_url}/api/experiments_runs/'
        payload = {
            "experiment_name": self.experiment_name,
            "number_of_configs": self.number_of_configs
        }
        headers = {'content-type': 'application/json'}
        try:
            response = requests.post(
                url, json=payload, headers=headers, auth=settings.REMOTE_LOGGING_CREDENTIALS)
            if response.status_code != 200:
                self.logger.error(
                    f'Failed to create new experiment run on remote server "{self.api_url}". Server returned {response.status_code} status code and following error:')
                self.logger.error(response.text)
            else:
                self.run_id = response.json()['run_id']
        except Exception as error:
            self.logger.error(
                f'Failed to create new experiment run on remote server "{self.api_url}" with following exception:')
            self.logger.error(str(error))
            self.logger.error(traceback.format_exc())

    def _setup_logger(self):
        logger = logging.getLogger('remote_logging')
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler(
            f'{settings.EXPERIMENT_BASE_LOGGING_DIR}/remote_logging.ERROR.log')
        formatter = logging.Formatter(
            '[%(levelname)s] %(asctime)s %(message)s')
        fh.setFormatter(formatter)
        fh.setLevel(logging.INFO)
        logging.getLogger("urllib3").level = logging.FATAL
        logging.getLogger("urllib3").disabled = True
        logger.addHandler(fh)
        logger.propagate = False
        self.logger = logger

    def terminate(self):
        self._alive = False

    def format(self, record: logging.LogRecord, **kwargs) -> dict:
        """Format log entry."""
        now = datetime.now(tz=settings.EXPERIMENT_TIMEZONE)
        message = {
            'timestamp_string': now.strftime(f'%Y-%m-%dT%H:%M:%S.0Z'),
            'timestamp': now.strftime(f'%Y-%m-%d-%H:%M:%S'),
            'experiment_version': self.experiment_version,
            'experiment_name': self.experiment_name,
            'logger': record.name,
            'config_name': kwargs.get('config_name', self.config_name),
            'filename': record.filename,
            'function_name': record.funcName,
            'line_number': record.lineno,
            'level': record.levelname,
            'level_value': record.levelno,
        }
        if isinstance(record.msg, Exception):
            stack_info = traceback.format_exc()
            message['stack_info'] = stack_info
            message['message'] = record.msg if isinstance(
                record.msg, str) else str(record.msg)
        elif isinstance(record.msg, str):
            message['message'] = record.msg
        else:
            message['message'] = str(record.msg)
        return message

    def flush(self, payload=None):

        if len(self.messages_queue) == 0:
            return
        headers = {'content-type': 'application/json'}
        url = f'{self.api_url}/api/logs/{self.run_id}/'
        lock.acquire()
        if payload is not None:
            self.messages_queue.append(payload)
        response = requests.post(
            url, json=self.messages_queue, headers=headers, auth=settings.REMOTE_LOGGING_CREDENTIALS)

        self.messages_queue = []
        if lock.locked():
            lock.release()
        if response.status_code != 200:
            self.logger.error(
                f'Failed to save logs to remote server "{self.api_url}". Server returned {response.status_code} status code and following error:')
            self.logger.error(response.text)

    def emit(self, record, **kwargs):
        """Save log entry to server."""
        try:
            message = self.format(record, **kwargs)
            lock.acquire()
            self.messages_queue.append(message)
            lock.release()
        except Exception as error:
            error_msg = f'Failed to format logs for remote server "{self.api_url}" with following exception:'
            self.logger.error(error_msg)
            self.logger.error(str(error))
            self.logger.error(traceback.format_exc())
            self.messages_queue.append(error_msg + str(error))
        finally:
            if lock.locked():
                lock.release()

    def log_step(self, config_name: str):
        try:
            headers = {'content-type': 'application/json'}
            url = f'{self.api_url}/api/experiments_runs/{self.run_id}/'
            lock.acquire()
            if config_name not in ExperimentConfig._configs_execution:
                ExperimentConfig._configs_execution[config_name] = {
                    'has_errors': False,
                }
            ExperimentConfig._configs_execution[config_name] = {
                **ExperimentConfig._configs_execution[config_name],
                **{
                    'config_name': config_name,
                    'steps': ExperimentConfig.steps_names,
                    'current_step': ExperimentConfig.current_step[config_name],
                    'steps_completed': ExperimentConfig.steps_completed_times[config_name]
                }
            }
            payload = {
                'configs_execution': ExperimentConfig._configs_execution
            }
            lock.release()
            response = requests.patch(
                url, json=payload, headers=headers, auth=settings.REMOTE_LOGGING_CREDENTIALS)
            if response.status_code != 200:
                self.logger.error(
                    f'Failed to save step log to remote server "{self.api_url}". Server returned {response.status_code} status code and following error:')
                self.logger.error(response.text)
        except Exception as error:
            self.logger.error(
                f'Failed to save step log to remote server "{self.api_url}". With following exception:')
            self.logger.error(str(error))
            self.logger.error(traceback.format_exc())
        finally:
            if lock.locked():
                lock.release()

    def _mark_experiment_run_as_with_errors(self, config_name: str, error_message: str, stack_trace: str = None):
        try:
            headers = {'content-type': 'application/json'}
            url = f'{self.api_url}/api/experiments_runs/{self.run_id}/'
            lock.acquire()
            if config_name not in ExperimentConfig._configs_execution:
                ExperimentConfig._configs_execution[config_name] = {}
            ExperimentConfig._configs_execution[config_name] = {
                **ExperimentConfig._configs_execution[config_name],
                **{
                    'config_name': config_name,
                    'steps': ExperimentConfig.steps_names,
                    'has_errors': True,
                    'finished': datetime.timestamp(datetime.now(tz=settings.EXPERIMENT_TIMEZONE)) * 1000,
                    'error_message': error_message,
                    'stack_trace': stack_trace
                }
            }
            payload = {
                'has_errors': True,
                'finished_configs': ExperimentConfig.completed_configs,
                'configs_execution': ExperimentConfig._configs_execution
            }
            if ExperimentConfig.completed_configs == ExperimentConfig.number_of_configs:
                payload['finished'] = datetime.now(tz=settings.EXPERIMENT_TIMEZONE).strftime(
                    f'%Y-%m-%d-%H:%M:%S')
            lock.release()
            response = requests.patch(
                url, json=payload, headers=headers, auth=settings.REMOTE_LOGGING_CREDENTIALS)
            if response.status_code != 200:
                self.logger.error(
                    f'Failed to save experiment run error info to remote server "{self.api_url}". Server returned {response.status_code} status code and following error:')
                self.logger.error(response.text)
        except Exception as error:
            self.logger.error(
                f'Failed to save experiment run error info to remote server "{self.api_url}". With following exception:')
            self.logger.error(str(error))
            self.logger.error(traceback.format_exc())
        finally:
            if lock.locked():
                lock.release()

    def _mark_experiment_as_finished(self, config_name: str):
        try:
            headers = {'content-type': 'application/json'}
            url = f'{self.api_url}/api/experiments_runs/{self.run_id}/'
            lock.acquire()

            if config_name not in ExperimentConfig._configs_execution:
                ExperimentConfig._configs_execution[config_name] = {}
            ExperimentConfig._configs_execution[config_name] = {
                **ExperimentConfig._configs_execution[config_name],
                **{
                    'config_name': config_name,
                    'steps': ExperimentConfig.steps_names,
                    'has_errors': False,
                    'finished': datetime.timestamp(datetime.now(tz=settings.EXPERIMENT_TIMEZONE)) * 1000,
                }
            }
            payload = {
                'finished_configs': ExperimentConfig.completed_configs,
                'configs_execution': ExperimentConfig._configs_execution
            }
            if ExperimentConfig.completed_configs == ExperimentConfig.number_of_configs:
                payload['finished'] = datetime.now(tz=settings.EXPERIMENT_TIMEZONE).strftime(
                    f'%Y-%m-%d-%H:%M:%S')
            lock.release()
            response = requests.patch(
                url, json=payload, headers=headers, auth=settings.REMOTE_LOGGING_CREDENTIALS)
            if response.status_code != 200:
                self.logger.error(
                    f'Failed to save experiment finished info to remote server "{self.api_url}". Server returned {response.status_code} status code and following error:')
                self.logger.error(response.text)
        except Exception as error:
            self.logger.error(
                f'Failed to save experiment finished info to remote server "{self.api_url}". With following exception:')
            self.logger.error(str(error))
            self.logger.error(traceback.format_exc())
        finally:
            if lock.locked():
                lock.release()

    def _mark_experiment_as_killed(self):
        try:
            headers = {'content-type': 'application/json'}
            url = f'{self.api_url}/api/experiments_runs/{self.run_id}/'
            payload = {
                'killed': True,
                'finished_configs': ExperimentConfig.completed_configs,
                'configs_execution': ExperimentConfig._configs_execution
            }
            payload['finished'] = datetime.now(tz=settings.EXPERIMENT_TIMEZONE).strftime(
                f'%Y-%m-%d-%H:%M:%S')
            response = requests.patch(
                url, json=payload, headers=headers, auth=settings.REMOTE_LOGGING_CREDENTIALS)
            if response.status_code != 200:
                self.logger.error(
                    f'Failed to save experiment kill info to remote server "{self.api_url}". Server returned {response.status_code} status code and following error:')
                self.logger.error(response.text)
        except Exception as error:
            self.logger.error(
                f'Failed to save experiment kill info to remote server "{self.api_url}". With following exception:')
            self.logger.error(str(error))
            self.logger.error(traceback.format_exc())
