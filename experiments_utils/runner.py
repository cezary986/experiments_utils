from logging import Logger, basicConfig
import logging
from time import sleep
import traceback
from .events.emitter import EventEmitter
from .events.events import *
from .context import ExperimentContext
from .remote_logging import RemoteLogsHandler, RemoteExperimentMonitor
from multiprocess.queues import Queue
from multiprocess.pool import Pool
from typing import Callable, Dict, List, Tuple
from . import conf


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

    def run(self, experiment):
        self._name: str = experiment.name
        self._version: str = experiment.version
        self._paramsets_names: str = list(experiment.paramsets.keys())
        self._dir_path: str = experiment.dir_path
        self._logger: str = experiment._logger
        self._event_queue: Queue = experiment._event_handler.event_queue
        self._event_queue: Queue = experiment._event_handler.event_queue
        self._function: Callable = experiment.function
        remote_logs_queue: Queue = experiment._remote_monitor.logs_queue if experiment._remote_monitor is not None else None

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
                self._logger.info(f'Starting experiment for paramset: "{context.paramset_name}"')
                event_emitter.emit_event(ParamsetStartEvent(
                    self._name, context.paramset_name))
                event_emitter.emit_event(ParamsetStartEvent(
                    self._name,
                    context.paramset_name,
                    event_type=f'{context.paramset_name}__PARAMSET_START'
                ))
                start_time = datetime.now(tz=conf.settings.EXPERIMENT_TIMEZONE)

                experiment_function(*experiment_params.values())

                self._logger.info(f'Finished experiment for paramset: "{context.paramset_name}". Took: {datetime.now(tz=conf.settings.EXPERIMENT_TIMEZONE) - start_time}')
                event_emitter.emit_event(ParamsetSuccessEvent(
                    self._name,
                    context.paramset_name,
                    event_type=f'{context.paramset_name}__PARAMSET_SUCCESS'
                ))
                event_emitter.emit_event(ParamsetSuccessEvent(
                    self._name, context.paramset_name))
            except Exception as exception:
                self._logger.info(f'Exception during experiment for paramset: "{context.paramset_name}". Took: {datetime.now(tz=conf.settings.EXPERIMENT_TIMEZONE) - start_time}')
                stack_trace: str = traceback.format_exc()
                context.logger.error(exception, exc_info=True)
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
                    logger=self._logger
                ),
                EventEmitter(self._event_queue)
            ) for paramset_name, paramset in experiment.paramsets.items()
        ]
        experiment_start_time = datetime.now(tz=conf.settings.EXPERIMENT_TIMEZONE)
        with Pool(experiment.n_jobs) as executor:
            executor.map_async(inner_wrapper, params_sets)
            experiment._event_handler.start_listening_for_events(
                len(params_sets))
        self._logger.info(
                f'Finished whole experiment "{self._name}". Took: {datetime.now(tz=conf.settings.EXPERIMENT_TIMEZONE) - experiment_start_time}')
