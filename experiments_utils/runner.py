import copy
import logging
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from logging import Logger, basicConfig
from time import sleep
from typing import Any, Callable, Dict, List, Tuple

from multiprocess.pool import Pool
from multiprocess.queues import Queue

from . import conf
from .context import ExperimentContext
from .events.emitter import EventEmitter
from .events.events import *
from .logs import run_from_ipython
from .remote_logging import RemoteExperimentMonitor, RemoteLogsHandler


class Runner:
    """Class for running experiment function with different paramsets
    among multiple processes
    """

    def __init__(
        self,
        settings,
    ) -> None:
        self._settings = settings
        self._name: str = None
        self._version: str = None
        self._paramsets_names: List[str] = None
        self._dir_path: str = None
        self._logger: Logger = None
        self._function: Callable = None
        self._event_queue: Queue = None

    def _initialize_plugins_for_experiment(self, experiment):
        for plugin in experiment.plugins.values():
            try:
                plugin.logger = logging.getLogger(f'plugin.{plugin.name}')
                plugin.experiment_initialize(experiment)
            except Exception as error:
                experiment.logger.error(
                    f'Failed to initialize plugin: "{plugin.name}" v{plugin.version} for experiment')
                plugin.logger.error(error, stack_info=True)

    def _finish_plugins_for_experiment(self, experiment):
        for plugin in experiment.plugins.values():
            try:
                plugin.experiment_finish(experiment)
            except Exception as error:
                experiment.logger.error(
                    f'Failed to finish plugin: "{plugin.name}" v{plugin.version} for experiment')
                plugin.logger.error(error, stack_info=True)

    def _initialize_plugins_for_paramset(self, context: ExperimentContext, params: Dict[str, Any]):
        for plugin in context.plugins.values():
            try:
                plugin.logger = logging.getLogger(f'plugin.{plugin.name}')
                plugin.paramset_start(context, params)
            except Exception as error:
                context.logger.error(
                    f'Failed to initialize plugin: "{plugin.name}" v{plugin.version} for paramset: "{context.paramset_name}"'
                )
                plugin.logger.error(error, stack_info=True)

    def _finish_plugins_for_paramset(self, context: ExperimentContext, error: Exception = None):
        for plugin in context.plugins.values():
            try:
                plugin.paramset_finish(context, error=error)
            except Exception as error:
                context.logger.error(
                    f'Failed to finish plugin: "{plugin.name}" v{plugin.version} for paramset: "{context.paramset_name}"'
                )
                plugin.logger.error(error, stack_info=True)

    def run(self, experiment):
        self._name: str = experiment.name
        self._version: str = experiment.version
        self._paramsets_names: str = list(map(lambda e: e[0], experiment.paramsets))
        self._dir_path: str = experiment.dir_path
        self._logger: str = experiment._logger
        self._event_queue: Queue = experiment._event_handler.event_queue
        self._event_queue: Queue = experiment._event_handler.event_queue
        self._function: Callable = experiment.function
        remote_logs_queue: Queue = experiment._remote_monitor.logs_queue if experiment._remote_monitor is not None else None

        self._initialize_plugins_for_experiment(experiment)

        def inner_wrapper(arg: Tuple[Dict[str, dict], Callable, ExperimentContext, EventEmitter]):
            conf.settings = self._settings
            experiment_params: Dict[str, dict] = arg[0]
            experiment_function: Callable = arg[1]
            context: ExperimentContext = arg[2]
            event_emitter: EventEmitter = arg[3]

            ExperimentContext.__GLOBAL_CONTEXT__ = context
            ExperimentContext.__EVENT_EMITTER__ = event_emitter

            context.logger.handlers = []
            remote_logger = None
            formatter = logging.Formatter(conf.settings.LOGS_FORMAT)
            for handler in context._logs_handlers:
                if isinstance(handler, logging.FileHandler):
                    file_handler = logging.FileHandler(handler.baseFilename)
                    file_handler.setFormatter(formatter)
                    file_handler.setLevel(handler.level)
                    context.logger.addHandler(file_handler)
            if remote_logs_queue is not None:
                remote_handler = RemoteLogsHandler(remote_logs_queue)
                remote_handler.setLevel(logging.DEBUG)
                remote_handler.setFormatter(formatter)
                context.logger.addHandler(remote_handler)
            basicConfig(level=context.logger.level)
            try:
                sleep(0.2)
                self._initialize_plugins_for_paramset(
                    context, experiment_params
                )
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(
                    logging.Formatter(conf.settings.LOGS_FORMAT))
                self._logger.addHandler(console_handler)
                self._logger.info(
                    f'Starting experiment for paramset: "{context.paramset_name}"')
                event_emitter.emit_event(ParamsetStartEvent(
                    self._name, context.paramset_name))
                event_emitter.emit_event(ParamsetStartEvent(
                    self._name,
                    context.paramset_name,
                    event_type=f'{context.paramset_name}__PARAMSET_START'
                ))
                start_time = datetime.now(tz=conf.settings.EXPERIMENT_TIMEZONE)

                result: Any = experiment_function(*experiment_params.values())

                self._logger.info(
                    f'Finished experiment for paramset: "{context.paramset_name}". Took: {datetime.now(tz=conf.settings.EXPERIMENT_TIMEZONE) - start_time}')
                self._finish_plugins_for_paramset(context)
                event_emitter.emit_event(ParamsetSuccessEvent(
                    self._name,
                    context.paramset_name,
                    event_type=f'{context.paramset_name}__PARAMSET_SUCCESS',
                    result=result
                ))
                event_emitter.emit_event(ParamsetSuccessEvent(
                    self._name, context.paramset_name, result=result))
            except Exception as exception:
                self._logger.info(
                    f'Exception during experiment for paramset: "{context.paramset_name}". Took: {datetime.now(tz=conf.settings.EXPERIMENT_TIMEZONE) - start_time}')
                stack_trace: str = traceback.format_exc()
                context.logger.error(exception, exc_info=True)
                self._finish_plugins_for_paramset(context, error=exception)
                event_emitter.emit_event(ParamsetErrorEvent(
                    self._name,
                    exception,
                    stack_trace,
                    context.paramset_name,
                    event_type=f'{context.paramset_name}__PARAMSET_ERROR'
                ))
                event_emitter.emit_event(ParamsetErrorEvent(
                    self._name, exception, stack_trace, context.paramset_name))
            finally:
                if remote_logger is not None:
                    remote_logger.flush()
                    remote_logger.terminate()
                event_emitter.emit_event(ParamsetEndEvent(
                    self._name,
                    context.paramset_name,
                    event_type=f'{context.paramset_name}__PARAMSET_END'
                ))
                event_emitter.emit_event(ParamsetEndEvent(
                    self._name, context.paramset_name))

        params_sets: List[Tuple[Dict[str, dict], Callable, ExperimentContext, EventEmitter]] = [
            (
                paramset,
                self._function,
                ExperimentContext(
                    name=self._name,
                    version=self._version,
                    paramsets_names=self._paramsets_names,
                    paramset_name=paramset_name,
                    current_dir=self._dir_path,
                    logs_dir=experiment.logs_dir,
                    logger=self._logger,
                    plugins={
                        key: plugin.clone() for key, plugin in experiment.plugins.items()
                    }
                ),
                EventEmitter(self._event_queue)
            ) for paramset_name, paramset in experiment.paramsets
        ]
        experiment_start_time = datetime.now(
            tz=conf.settings.EXPERIMENT_TIMEZONE)

        if run_from_ipython():
            pool = ThreadPoolExecutor(max_workers=experiment.n_jobs)
            experiment._logger.warning(
                'Running from Interactive Interpreter which is not supporting multiprocessing, will use threading instead.')
            setattr(pool, 'map_async', pool.map)
        else:
            pool = Pool(experiment.n_jobs)

        with pool as executor:
            executor.map_async(inner_wrapper, params_sets)
            experiment._event_handler.start_listening_for_events(
                len(params_sets))
        self._finish_plugins_for_experiment(experiment)
        self._logger.info(
            f'Finished whole experiment "{self._name}". Took: {datetime.now(tz=conf.settings.EXPERIMENT_TIMEZONE) - experiment_start_time}')
