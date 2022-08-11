from __future__ import annotations
from logging import Logger
import logging
from time import sleep
from typing import Any, Callable, Dict
import os
from datetime import datetime
from .logs import configure_experiment_logger, configure_logging
from . import conf
from .events.emitter import EventEmitter
from .events.handler import EventHandler
from .events import EventTypes
from .events.events import *
from .runner import Runner
from .store import Store
from .remote_logging import RemoteExperimentMonitor, RemoteLogsHandler
from .state import ExperimentStateManager, ExperimentState
from .context import ExperimentContext
import inspect
from multiprocess import Manager
from multiprocess.queues import Queue


class Experiment:
    """Wrapping class for experiment function.
    It allows:
        * running experimen function with multiple sets of parameters on multiple processes
        * accessing basic experiment info like name or version
        * accessing experiment logger
        * listening to different experiment events - to see
    """

    def __init__(
        self,
        function,
        name: str,
        paramsets: Dict[str, Dict[str, Any]] = None,
        _file_: str = None,
        n_jobs: int = 4,
        version: str = None
    ) -> None:
        self.name: str = name
        self.paramsets: Dict[str, Dict[str, Any]] = paramsets
        self._file_: str = _file_
        self.n_jobs: str = n_jobs
        self.version: str = version

        self._event_queue: Queue = None
        self._event_handler: EventHandler = EventHandler()
        self._event_emitter: EventEmitter = None
        if _file_ is None:
            _file_ = inspect.stack()[2][1]
        self.dir_path = os.path.dirname(os.path.realpath(_file_))
        self.function: Callable = function

        self._logger: Logger = logging.getLogger(self.name)
        self._logger.setLevel(logging.DEBUG)
        self._remote_monitor: RemoteExperimentMonitor = None
        self.state = None
        state_manager = None

    def on_event(self, event_type: EventTypes):
        """Helper decorator to adding event listeners.

        Args:
            event_type (EventTypes): event type to listen for
        """
        return self._event_handler.on_event(event_type)

    def add_event_listener(self, event_type: EventTypes, handler: Callable):
        """Adds event listener

        Args:
            event_type (EventTypes): event type
            handler (Callable): listener handler function
        """
        return self._event_handler.add_event_listener(event_type, handler)

    def _initilize_experiment_logger(self):
        from . import settings as settings
        conf.settings = settings
        current_time_str: str = datetime.now(
            tz=settings.EXPERIMENT_TIMEZONE).strftime("%d.%m.%Y_%H.%M.%S")

        logs_dir_name: str = f'{current_time_str}'
        if self.version is not None:
            logs_dir_name += f'v{self.version}'

        configure_logging(self._file_, logs_dir_name, self.dir_path)
        configure_experiment_logger(self._logger)

    def _initialize_remote_logger(self):
        from . import settings as settings
        if settings.REMOTE_LOGGING_ENABLED:
            self._remote_monitor = RemoteExperimentMonitor()
            self._remote_monitor.bootstrap(experiment=self)
            self._remote_monitor.run()
            self._logger.addHandler(RemoteLogsHandler(
                self._remote_monitor.logs_queue))
            self._logger.debug(
                f'Forwarding experiment logs to remote server: ' +
                f'"{settings.REMOTE_LOGGING_URL}" run_id = {self._remote_monitor._run_id}')

    def _run(self, paramsets: Dict[str, Dict[str, Any]] = None):
        if paramsets is None and self.paramsets is None:
            raise Exception('''No paramsets were passed to experiment. Pass them either when calling experiment or in decorator.
    
Example:

    @experiment(name="example_experiment") 
    def example_experiment(a: int, b: int):
        ...

    if __name__ == '__main__:
        example_experiment({
-->        'paramset_1': {'a': 1, 'b': 2},
            ...
        })

Alternatively:

    @experiment(
        name="example_experiment",
-->     paramsets={
            'paramset_1': {'a': 1, 'b': 2},
            ...
        }
    ) 
    def example_experiment(a: int, b: int):
        ...

    if __name__ == '__main__:
        example_experiment()
                ''')
        if paramsets is not None:
            self.paramsets = paramsets
        self.state = ExperimentState(
            self.name, self.version, list(self.paramsets.keys()))
        state_manager = ExperimentStateManager(self.state)
        state_manager.bootstrap(experiment=self)

        from . import settings
        conf.settings = settings
        logging.basicConfig(level=self._logger.level)
        self._initilize_experiment_logger()

        ExperimentContext.__GLOBAL_CONTEXT__ = ExperimentContext(
            name=self.name,
            version=self.version,
            paramsets_names=list(self.paramsets.keys()),
            paramset_name=None,
            current_dir=self.dir_path,
            logger=self._logger
        )

        event_queue: Queue = Manager().Queue()
        self._event_handler.event_queue = event_queue
        self._event_emitter = EventEmitter(event_queue=event_queue)

        self._initialize_remote_logger()

        self._event_emitter.emit_event(ExperimentStartEvent(self.name))
        self._event_emitter.emit_event(ExperimentStartEvent(
            self.name,
            event_type=f'{self.name}__EXPERIMENT_START'
        ))

        runner = Runner(conf.settings)
        try:
            self._logger.debug(
                f'Starting experiment "{self.name}" v{self.version} (n_paramsets: {len(self.paramsets)})')
            runner.run(experiment=self)
        except KeyboardInterrupt:
            if self._remote_monitor is not None:
                self._remote_monitor._mark_experiment_as_killed()
            self._event_emitter.emit_event(ExperimentEndEvent(self.name))
        finally:
            if self._remote_monitor is not None:
                self._remote_monitor.terminate()
            ExperimentContext.__GLOBAL_CONTEXT__ = None

    __call__ = _run


def experiment(
    name: str,
    paramsets: Dict[str, Dict[str, Any]] = None,
    _file_: str = None,
    n_jobs: int = 4,
    version: str = None
):
    """Decorator for experiment functions

    Args:
        name (str): Name of experiment (used for generating results)
        paramsets (Dict[str, Dict[str, Any]]): dictionary containing sets of parameters for experiment to run with
        _file_ (str) optional __file__ variable from experiment main file. It will be automatically detected.
        max_threads (int) max number of threard, Default 8
        version (str) version string, Default is None
    """
    def wrapper(function):
        return Experiment(
            name=name,
            paramsets=paramsets,
            _file_=_file_,
            n_jobs=n_jobs,
            version=version,

            function=function
        )
    return wrapper
