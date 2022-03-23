from multiprocessing import context
import threading
from typing import List
from datetime import datetime
import logging
from typing import Any
from concurrent.futures import ThreadPoolExecutor
from logging import Logger
from .logging import configure_logging, get_experiment_logger, get_step_logger
from .remote_logging import RemoteLogsHandler
from . import settings
import os
import sys
import pickle
import traceback

logging.basicConfig(level=logging.DEBUG)
lock: threading.Lock = threading.Lock()


class ExperimentConfig:
    main_logger: Logger = None
    remote_log_handler: RemoteLogsHandler = None
    steps_names: List[str] = []
    steps_count: int = 0
    steps_index: dict = {}
    steps_completed_times: dict = {}
    _last_step_index: int = 0
    completed_configs: int = 0
    number_of_configs: int = 0

    _configs_execution: dict = {}


class ExperimentContext:

    def __init__(self, config_name: str, current_dir: str) -> None:
        self._config_name: str = config_name
        self._current_dir: str = current_dir

    @property
    def config_name(self) -> str:
        return self._config_name

    @property
    def current_dir(self) -> str:
        return self._current_dir


def experiment(
    name: str,
    configurations: dict,
    _file_,
    max_threads: int = settings.THREADS_LIMIT,
    version: str = None
):
    """Decorator for experiment functions

    Parameters:
    name (str): Name of experiment (used for generating results)
    configurations (List[dict]): List with dictionaries containing params for experiment
    logger (Logger) optional configured logger
    max_threads (int) max number of threard, Default 8
    version (str) version string
   """
    dir_path = os.path.dirname(os.path.realpath(_file_))
    settings.dir_path = dir_path
    current_time_str: str = datetime.now(
        tz=settings.EXPERIMENT_TIMEZONE).strftime("%d.%m.%Y_%H.%M.%S")
    logs_dir_name: str = f'{current_time_str}v{version}'

    configure_logging(__file__, logs_dir_name, dir_path)

    logger: Logger = get_experiment_logger(name)
    logger.setLevel(logging.DEBUG)
    ExperimentConfig.main_logger = logger

    remote_logs_handler: RemoteLogsHandler = None
    if settings.REMOTE_LOGGING_ENABLED:
        remote_logs_handler = RemoteLogsHandler(
            experiment_name=name,
            number_of_configs=len(configurations),
            experiment_version=version
        )
        logger.debug(
            f'Forwarding experiment logs to remote server: "{settings.REMOTE_LOGGING_URL}" run_id = {remote_logs_handler.run_id}')
        logger.addHandler(remote_logs_handler)
        ExperimentConfig.remote_log_handler = remote_logs_handler

    logger.debug(
        f'Starting experiment "{name}" v{version} (n_configurations: {len(configurations)}, n_steps: {ExperimentConfig.steps_count})')

    def decorator(function):
        def wrapper():
            ExperimentConfig.steps_names = sorted(ExperimentConfig.steps_names)
            ExperimentConfig.number_of_configs = len(configurations.keys())
            configs_list: list = []
            experiment_start_time = datetime.now(
                tz=settings.EXPERIMENT_TIMEZONE)
            for key in configurations:
                ExperimentConfig.steps_completed_times[key] = {
                    step_name: None for step_name in ExperimentConfig.steps_names}
            for key in configurations:
                params = configurations[key]
                params['context'] = ExperimentContext(
                    config_name=key,
                    current_dir=dir_path
                )
                configs_list.append(params)

            def inner_wrapper(experiment_params: dict):
                global lock
                context: ExperimentContext = experiment_params['context']
                config_name: str = context.config_name

                try:
                    start_time = datetime.now(
                        tz=settings.EXPERIMENT_TIMEZONE)
                    res = function(**experiment_params, logger=logger)
                    lock.acquire()
                    ExperimentConfig.completed_configs = ExperimentConfig.completed_configs + 1
                    lock.release()
                    logger.info(
                        f'Finished experiment for config "{config_name}". Took: {datetime.now(tz=settings.EXPERIMENT_TIMEZONE) - start_time}')
                    if remote_logs_handler is not None:
                        remote_logs_handler._mark_experiment_as_finished(
                            config_name)
                    return res
                except Exception as error:
                    logger.error(
                        f'Exception during experiment for config: "{config_name}". Took: {datetime.now(tz=settings.EXPERIMENT_TIMEZONE) - start_time}, details bellow:')
                    logger.error(error)
                    stack_trace = traceback.format_exc()
                    logger.error(stack_trace)
                    lock.acquire()
                    ExperimentConfig.completed_configs = ExperimentConfig.completed_configs + 1
                    lock.release()
                    if remote_logs_handler is not None:
                        remote_logs_handler._mark_experiment_run_as_with_errors(
                            config_name=config_name,
                            error_message=str(error),
                            stack_trace=stack_trace)

            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                try:
                    results = executor.map(inner_wrapper, configs_list)
                    for result in results:
                        _ = result
                except KeyboardInterrupt as error:
                    logger.error(KeyboardInterrupt())
                    logger.error('Experiment finished with keyboard interrupt')
                    if remote_logs_handler is not None:
                        remote_logs_handler.flush()
                        remote_logs_handler._mark_experiment_as_killed()
                    # hard kill
                    while True:
                        os._exit(1)
                        sys.exit()
            logger.debug(
                f'Finished whole experiment Took: {datetime.now(tz=settings.EXPERIMENT_TIMEZONE) - experiment_start_time}')
            if remote_logs_handler is not None:
                remote_logs_handler.flush()
                remote_logs_handler.terminate()
            return
        return wrapper
    return decorator


def step(name: str):
    """Decorator for experiment step
    It allows to replay step with last params
   """

    ExperimentConfig.steps_names.append(name)
    ExperimentConfig.steps_count += 1

    def decorator(function):

        def wrapper(*args, **kwargs):
            step_index: int = ExperimentConfig.steps_index.get(
                name, ExperimentConfig._last_step_index)
            ExperimentConfig.steps_index[name] = step_index
            ExperimentConfig._last_step_index += 1
            config_key: str = kwargs['context'].config_name

            logger = get_step_logger(name, config_key)
            ExperimentConfig.main_logger.info(
                f'Started step "{name}" for config "{config_key}"')
            start_time = datetime.now(tz=settings.EXPERIMENT_TIMEZONE)
            if ExperimentConfig.remote_log_handler is not None:
                ExperimentConfig.remote_log_handler.log_step(
                    config_key, step_index)

            result = function(*args, **kwargs, logger=logger)

            now = datetime.now(tz=settings.EXPERIMENT_TIMEZONE)
            ExperimentConfig.steps_completed_times[config_key][name] = now.strftime(
                f'%Y-%m-%d-%H:%M:%S')
            ExperimentConfig.main_logger.info(
                f'Finished step "{name}" for config "{config_key}". Took: {now - start_time}')
            logger.debug(
                f'Finished step "{name}" for config "{config_key}". Took: {now - start_time}')

            step_index += 1
            if ExperimentConfig.remote_log_handler is not None:
                ExperimentConfig.remote_log_handler.log_step(
                    config_key, step_index)
            return result
        return wrapper
    return decorator


class State(object):

    def __init__(self, context: ExperimentContext) -> None:
        object.__setattr__(self, '__variables__', {})
        params_file_path = f'{context.current_dir}/_cache/{context.config_name}'
        object.__setattr__(self, '__params_base_dir_path', params_file_path)

    def __getattribute__(self, name: str) -> Any:
        if name == '__variables__':
            return object.__getattribute__(self, '__variables__')
        if name == '_State__retrieve_variable':
            return object.__getattribute__(self, '_State__retrieve_variable')
        if name == '_State__save_variable':
            return object.__getattribute__(self, '_State__save_variable')
        if name == '__class__':
            return State
        if name == '__module__':
            return __file__
        if name == '__dict__':
            return {}
        else:
            return self.__retrieve_variable(name)

    def __setattr__(self, name: str, value: Any) -> None:
        self.__save_variable(name, value)

    def __save_variable(self, name: str, value: Any):
        os.makedirs(object.__getattribute__(
            self, '__params_base_dir_path'), exist_ok=True)
        path = f'{object.__getattribute__(self, "__params_base_dir_path")}/{name}.pickle'
        with open(path, 'wb+') as params_file:
            pickle.dump(value, params_file)

    def __retrieve_variable(self, name: str) -> Any:
        var_file_path = f'{object.__getattribute__(self, "__params_base_dir_path")}/{name}.pickle'
        if os.path.exists(var_file_path):
            with open(var_file_path, 'rb') as var_file:
                return pickle.load(var_file)
        else:
            raise NameError(f"name '{name}' is not defined")
