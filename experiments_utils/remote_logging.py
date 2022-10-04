from ctypes import Union
import logging
import traceback
from datetime import datetime
from typing import Any, List, Tuple

from .state import ExperimentState, ParamSetState
from .events.event_types import EventTypes
from .events import *
from .context import ExperimentContext
from . import conf
from threading import Thread
from multiprocess.queues import Queue
from multiprocess import Process
from multiprocess import Manager
import requests
import time


def _setup_internal_logger(_settings: Any):
    logger = logging.getLogger('remote_logging')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(
        f'{_settings.EXPERIMENT_BASE_LOGGING_DIR}/remote_logging.ERROR.log')
    formatter = logging.Formatter(
        '[%(levelname)s] %(asctime)s %(message)s')
    fh.setFormatter(formatter)
    fh.setLevel(logging.INFO)
    logging.getLogger("urllib3").level = logging.FATAL
    logging.getLogger("urllib3").disabled = True
    logger.addHandler(fh)
    logger.propagate = False
    return logger


class RemoteLogsHandler(logging.StreamHandler):

    def __init__(self, logs_queue: Queue) -> None:
        logging.StreamHandler.__init__(self)
        self._logger: logging.Logger = _setup_internal_logger(conf.settings)
        self._logs_queue: Queue = logs_queue

    def format(self, record: logging.LogRecord, **kwargs) -> dict:
        """Format log entry."""
        now = datetime.now(tz=conf.settings.EXPERIMENT_TIMEZONE)
        message = {
            'timestamp_string': now.strftime(f'%Y-%m-%dT%H:%M:%S.0Z'),
            'timestamp': now.strftime(f'%Y-%m-%d-%H:%M:%S'),
            'experiment_version': ExperimentContext.__GLOBAL_CONTEXT__.version,
            'experiment_name': ExperimentContext.__GLOBAL_CONTEXT__.name,
            'logger': record.name,
            'config_name': ExperimentContext.__GLOBAL_CONTEXT__.paramset_name if ExperimentContext.__GLOBAL_CONTEXT__ is not None else None,
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

    def emit(self, record: logging.LogRecord, **kwargs):
        """Save log entry to server."""
        try:
            message = self.format(record, **kwargs)
            self._logs_queue.put_nowait(message)
        except Exception as error:
            error_msg = f'Failed to format logs for remote server "{self.api_url}" with following exception:'
            self._logger.error(error_msg)
            self._logger.error(str(error))
            self._logger.error(traceback.format_exc())


class RemoteExperimentMonitor:

    DEATH_PILL: str = 'DEATH_PILL'

    """Logging handler writing logs to remote server."""

    def __init__(self):
        from . import settings as settings

        self.api_url: str = settings.REMOTE_LOGGING_URL
        self._run_id: int = None
        self._messages_queue: List[logging.LogRecord] = []
        self._logger: logging.Logger = _setup_internal_logger(conf.settings)
        self._configs_execution: dict = {}
        self._experiment_state: ExperimentState = None

        self._logs_queue: Queue = Manager().Queue()

        def run_function(arg: Tuple[Queue, int, Any]):
            messages_queue: List[logging.LogRecord] = []
            logs_queue: Queue = arg[0]
            run_id: int = arg[1]
            _settings = arg[2]
            api_url: str = _settings.REMOTE_LOGGING_URL
            credentials: Tuple[str, str] = _settings.REMOTE_LOGGING_CREDENTIALS
            logger: logging.Logger = _setup_internal_logger(_settings)

            def on_terminate():
                RemoteExperimentMonitor._flush(
                    messages_queue,
                    logger,
                    api_url,
                    run_id,
                    credentials
                )

            logger.info('Log collecting process started')

            def flush_function():
                logger.info('Flush thread started')
                while True:
                    time.sleep(settings.REMOTE_LOGGING_THROTTLE)
                    RemoteExperimentMonitor._flush(
                        messages_queue,
                        logger,
                        api_url,
                        run_id,
                        credentials
                    )
            flush_thread = Thread(target=flush_function, daemon=True)
            flush_thread.start()
            while True:
                record: Union[logging.LogRecord, str] = logs_queue.get()
                if record == RemoteExperimentMonitor.DEATH_PILL:
                    on_terminate()
                    return
                else:
                    messages_queue.append(record)

        self._fetch_run_id()
        self._process: Process = Process(
            target=run_function, args=[(
                self._logs_queue,
                self._run_id,
                conf.settings
            )])

    @property
    def logs_queue(self) -> Queue:
        return self._logs_queue

    def bootstrap(self, experiment):
        self._experiment_state: ExperimentState = experiment.state

        @experiment.on_event(EventTypes.EXPERIMENT_START)
        def _(event: ExperimentStartEvent):
            self._create_experiment()

        @experiment.on_event(EventTypes.EXPERIMENT_PARAMSET_START)
        def _(event: ParamsetEndEvent):
            self._mark_experiment_as_started(
                paramset_name=event.paramset_name)

        @experiment.on_event(EventTypes.EXPERIMENT_PARAMSET_SUCCESS)
        def _(event: ParamsetEndEvent):
            self._mark_experiment_as_finished(
                paramset_name=event.paramset_name)

        @experiment.on_event(EventTypes.EXPERIMENT_PARAMSET_ERROR)
        def _(event: ParamsetErrorEvent):
            self._mark_experiment_run_as_with_errors(
                paramset_name=event.paramset_name,
                error_message=str(event.exception),
                stack_trace=event.stack_trace
            )

        @experiment.on_event(EventTypes.STEP_END)
        def _(event: StepEndEvent):
            self._log_step(
                config_name=event.paramset_name
            )

    def run(self):
        self._process.start()

    def terminate(self):
        self.logs_queue.put_nowait(RemoteExperimentMonitor.DEATH_PILL)
        self._logger.info('Log collecting process terminated')

    @staticmethod
    def _flush(
        messages_queue: List[logging.LogRecord],
        logger: logging.Logger,
        api_url: str,
        run_id: int,
        credentials: Tuple[str, str]
    ):
        if len(messages_queue) == 0:
            return
        headers = {'content-type': 'application/json'}
        url = f'{api_url}/api/logs/{run_id}/'
        response = requests.post(
            url, json=messages_queue, headers=headers, auth=credentials)
        messages_queue.clear()
        if response.status_code != 200:
            logger.error(
                f'Failed to save logs to remote server "{api_url}". Server returned {response.status_code} status code and following error:')
            logger.error(response.text)
        logger.info('Flushed')

    def _create_experiment(self):
        """Create experiment on server (or does nothing if already exists)."""
        url = f'{self.api_url}/api/experiments/'
        payload = {"name": ExperimentContext.__GLOBAL_CONTEXT__.name}
        headers = {'content-type': 'application/json'}
        try:
            response = requests.post(
                url, json=payload, headers=headers, auth=conf.settings.REMOTE_LOGGING_CREDENTIALS)

            if response.status_code != 200 or (response.status_code == 400 and ('already exists' in response.text)):
                return
            else:
                self._logger.error(
                    f'Failed to create new experiment on remote server "{self.api_url}". Server returned {response.status_code} status code and following error:')
                self._logger.error(response.text)
        except Exception as error:
            self._logger.error(
                f'Failed to create new experiment on remote server "{self.api_url}" with following exception:')
            self._logger.error(str(error))
            self._logger.error(traceback.format_exc())

    def _fetch_run_id(self):
        """Save log entry to server."""
        self._create_experiment()
        url = f'{self.api_url}/api/experiments_runs/'
        payload = {
            "experiment_name": ExperimentContext.__GLOBAL_CONTEXT__.name,
            "number_of_configs": len(ExperimentContext.__GLOBAL_CONTEXT__.paramsets_names)
        }
        headers = {'content-type': 'application/json'}
        try:
            response = requests.post(
                url, json=payload, headers=headers, auth=conf.settings.REMOTE_LOGGING_CREDENTIALS)
            if response.status_code != 200:
                self._logger.error(
                    f'Failed to create new experiment run on remote server "{self.api_url}". Server returned {response.status_code} status code and following error:')
                self._logger.error(response.text)
            else:
                self._run_id = response.json()['run_id']
        except Exception as error:
            self._logger.error(
                f'Failed to create new experiment run on remote server "{self.api_url}" with following exception:')
            self._logger.error(str(error))
            self._logger.error(traceback.format_exc())

    def _log_step(self, config_name: str):
        try:
            paramset_state: ParamSetState = self._experiment_state.get_paramset_state(
                config_name)
            headers = {'content-type': 'application/json'}
            url = f'{self.api_url}/api/experiments_runs/{self._run_id}/'
            if config_name not in self._configs_execution:
                self._configs_execution[config_name] = {
                    'has_errors': False,
                }
            steps_completed = {}
            for step_name in self._experiment_state.steps_names:
                if paramset_state._steps_state[step_name].finished is not None:
                    steps_completed[step_name] = paramset_state._steps_state[step_name].finished.strftime(
                        f'%Y-%m-%d-%H:%M:%S')
            self._configs_execution[config_name] = {
                **self._configs_execution.get(config_name, {}),
                **{
                    'config_name': config_name,
                    'steps': self._experiment_state.steps_names,
                    'current_step': paramset_state.current_step,
                    'steps_completed': steps_completed
                }
            }
            payload = {
                'configs_execution': self._configs_execution
            }
            response = requests.patch(
                url, json=payload, headers=headers, auth=conf.settings.REMOTE_LOGGING_CREDENTIALS)
            if response.status_code != 200:
                self._logger.error(
                    f'Failed to save step log to remote server "{self.api_url}". Server returned {response.status_code} status code and following error:')
                self._logger.error(response.text)
        except Exception as error:
            self._logger.error(
                f'Failed to save step log to remote server "{self.api_url}". With following exception:')
            self._logger.error(str(error))
            self._logger.error(traceback.format_exc())

    def _mark_experiment_run_as_with_errors(self, paramset_name: str, error_message: str, stack_trace: str = None):
        try:
            headers = {'content-type': 'application/json'}
            url = f'{self.api_url}/api/experiments_runs/{self._run_id}/'
            if paramset_name not in self._configs_execution:
                self._configs_execution[paramset_name] = {}
            self._configs_execution[paramset_name] = {
                **self._configs_execution.get(paramset_name, {}),
                **{
                    'config_name': paramset_name,
                    'steps': self._experiment_state.steps_names,
                    'has_errors': True,
                    'finished': datetime.timestamp(datetime.now(tz=conf.settings.EXPERIMENT_TIMEZONE)) * 1000,
                    'error_message': error_message,
                    'stack_trace': stack_trace
                }
            }
            finished_paramsets: int = len(
                self._experiment_state.finished_paramsets) + len(self._experiment_state.failed_paramsets)
            payload = {
                'has_errors': True,
                'finished_configs': finished_paramsets,
                'configs_execution': self._configs_execution
            }
            if finished_paramsets == len(self._experiment_state.paramsets_names):
                payload['finished'] = datetime.now(tz=conf.settings.EXPERIMENT_TIMEZONE).strftime(
                    f'%Y-%m-%d-%H:%M:%S')
            response = requests.patch(
                url, json=payload, headers=headers, auth=conf.settings.REMOTE_LOGGING_CREDENTIALS)
            if response.status_code != 200:
                self._logger.error(
                    f'Failed to save experiment run error info to remote server "{self.api_url}". Server returned {response.status_code} status code and following error:')
                self._logger.error(response.text)
        except Exception as error:
            self._logger.error(
                f'Failed to save experiment run error info to remote server "{self.api_url}". With following exception:')
            self._logger.error(str(error))
            self._logger.error(traceback.format_exc())

    def _mark_experiment_as_finished(self, paramset_name: str):
        try:
            headers = {'content-type': 'application/json'}
            url = f'{self.api_url}/api/experiments_runs/{self._run_id}/'

            self._configs_execution[paramset_name] = {
                **self._configs_execution.get(paramset_name, {}),
                **{
                    'config_name': paramset_name,
                    'steps': self._experiment_state.steps_names,
                    'has_errors': False,
                    'finished': datetime.timestamp(datetime.now(tz=conf.settings.EXPERIMENT_TIMEZONE)) * 1000,
                }
            }
            finished_paramsets: int = len(
                self._experiment_state.finished_paramsets) + len(self._experiment_state.failed_paramsets)
            payload = {
                'finished_configs': finished_paramsets,
                'configs_execution': self._configs_execution
            }
            if finished_paramsets == len(self._experiment_state.paramsets_names):
                payload['finished'] = datetime.now(tz=conf.settings.EXPERIMENT_TIMEZONE).strftime(
                    f'%Y-%m-%d-%H:%M:%S')
            response = requests.patch(
                url, json=payload, headers=headers, auth=conf.settings.REMOTE_LOGGING_CREDENTIALS)
            if response.status_code != 200:
                self._logger.error(
                    f'Failed to save experiment finished info to remote server "{self.api_url}". Server returned {response.status_code} status code and following error:')
                self._logger.error(response.text)
        except Exception as error:
            self._logger.error(
                f'Failed to save experiment finished info to remote server "{self.api_url}". With following exception:')
            self._logger.error(str(error))
            self._logger.error(traceback.format_exc())
    
    def _mark_experiment_as_started(self, paramset_name: str):
        try:
            headers = {'content-type': 'application/json'}
            url = f'{self.api_url}/api/experiments_runs/{self._run_id}/'

            self._configs_execution[paramset_name] = {
                **self._configs_execution.get(paramset_name, {}),
                **{
                    'config_name': paramset_name,
                    'steps': self._experiment_state.steps_names,
                    'has_errors': False,
                    'started': datetime.timestamp(datetime.now(tz=conf.settings.EXPERIMENT_TIMEZONE)) * 1000,
                }
            }
            finished_paramsets: int = len(
                self._experiment_state.finished_paramsets) + len(self._experiment_state.failed_paramsets)
            payload = {
                'finished_configs': finished_paramsets,
                'configs_execution': self._configs_execution
            }
            if finished_paramsets == len(self._experiment_state.paramsets_names):
                payload['finished'] = datetime.now(tz=conf.settings.EXPERIMENT_TIMEZONE).strftime(
                    f'%Y-%m-%d-%H:%M:%S')
            response = requests.patch(
                url, json=payload, headers=headers, auth=conf.settings.REMOTE_LOGGING_CREDENTIALS)
            if response.status_code != 200:
                self._logger.error(
                    f'Failed to save experiment finished info to remote server "{self.api_url}". Server returned {response.status_code} status code and following error:')
                self._logger.error(response.text)
        except Exception as error:
            self._logger.error(
                f'Failed to save experiment finished info to remote server "{self.api_url}". With following exception:')
            self._logger.error(str(error))
            self._logger.error(traceback.format_exc())

    def _mark_experiment_as_killed(self):
        try:
            headers = {'content-type': 'application/json'}
            url = f'{self.api_url}/api/experiments_runs/{self._run_id}/'
            finished_paramsets: int = len(
                self._experiment_state.finished_paramsets) + len(self._experiment_state.failed_paramsets)
            payload = {
                'killed': True,
                'finished_configs': finished_paramsets,
                'configs_execution': self._configs_execution
            }
            payload['finished'] = datetime.now(tz=conf.settings.EXPERIMENT_TIMEZONE).strftime(
                f'%Y-%m-%d-%H:%M:%S')
            response = requests.patch(
                url, json=payload, headers=headers, auth=conf.settings.REMOTE_LOGGING_CREDENTIALS)
            if response.status_code != 200:
                self._logger.error(
                    f'Failed to save experiment kill info to remote server "{self.api_url}". Server returned {response.status_code} status code and following error:')
                self._logger.error(response.text)
        except Exception as error:
            self._logger.error(
                f'Failed to save experiment kill info to remote server "{self.api_url}". With following exception:')
            self._logger.error(str(error))
            self._logger.error(traceback.format_exc())
