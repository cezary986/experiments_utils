from __future__ import annotations
from logging import Logger
import logging
from typing import Any, Callable, Dict, List, Tuple
import os
from datetime import datetime
import inspect
from multiprocess import Manager
from multiprocess.queues import Queue
from experiments_utils.logs import \
    run_from_ipython, \
    debugger_is_active, \
    configure_logging, \
    configure_experiment_logger
from experiments_utils import conf
from experiments_utils.events.emitter import EventEmitter
from experiments_utils.events.handler import EventHandler
from experiments_utils.events import EventTypes
from experiments_utils.events.events import ExperimentStartEvent, ExperimentEndEvent
from experiments_utils.runner import Runner
from experiments_utils.remote_logging import RemoteExperimentMonitor, RemoteLogsHandler
from experiments_utils.state import ExperimentStateManager, ExperimentState
from experiments_utils.context import ExperimentContext
from experiments_utils.plugin import Plugin


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
        paramsets: List[Tuple[str, Dict[str, Any]]] = None,
        _file_: str = None,
        n_jobs: int = 4,
        version: str = None
    ) -> None:
        self.name: str = name
        self.paramsets: List[Tuple[str, Dict[str, Any]]] = paramsets

        self.n_jobs: int = n_jobs
        self.version: str = version

        self.results: Dict[str, Any]

        self._event_queue: Queue = None

        self._event_emitter: EventEmitter = None

        self._file_: str = _file_
        self.dir_path: str = self._resolve_active_dir()
        self.function: Callable = function

        self._logger: Logger = logging.getLogger(self.name)
        self._event_handler: EventHandler = EventHandler(self.logger)
        self._logger.setLevel(logging.DEBUG)
        self._remote_monitor: RemoteExperimentMonitor = None
        self.state = None
        self.plugins: Dict = {}

    @property
    def logger(self) -> Logger:
        return self._logger

    def add_plugin(self, plugin: Plugin):
        if plugin.name not in self.plugins:
            self.plugins[plugin.name] = plugin
        else:
            raise ValueError(
                f'Failed to add multiple plugins with same name: "{plugin.name}"'
            )

    def _resolve_active_dir(self) -> str:
        if run_from_ipython():
            # when running from ipython __file__ inspect stact won't return correct path
            return os.path.abspath(os.curdir)

        if self._file_ is None:
            self. _file_ = inspect.stack()[2][1]
        return os.path.dirname(os.path.realpath(self._file_))

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
        from experiments_utils import settings  # pylint: disable=import-outside-toplevel
        conf.settings = settings
        current_time_str: str = datetime.now(
            tz=settings.EXPERIMENT_TIMEZONE).strftime("%d.%m.%Y_%H.%M.%S")

        logs_dir_name: str = f'{current_time_str}'
        if self.version is not None:
            logs_dir_name += f'v{self.version}'

        configure_logging(self._file_, logs_dir_name, self.dir_path)
        configure_experiment_logger(self._logger)

    def _initialize_remote_logger(self):
        from experiments_utils import settings  # pylint: disable=import-outside-toplevel
        if settings.REMOTE_LOGGING_ENABLED and not debugger_is_active():
            self._remote_monitor = RemoteExperimentMonitor()
            self._remote_monitor.bootstrap(experiment=self)
            self._remote_monitor.run()
            self._logger.addHandler(RemoteLogsHandler(
                self._remote_monitor.logs_queue))
            self._logger.debug(
                'Forwarding experiment logs to remote server: ' +
                f'"{settings.REMOTE_LOGGING_URL}" run_id = {self._remote_monitor._run_id}')

    def _run(self, paramsets: List[Tuple[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Runs experiment

        Returns:
            Dict[str, Any]: Experiment results returned from each calling of experiment function group by dictionary
                where paramset names are keys.
        """
        if paramsets is None and self.paramsets is None:
            raise ValueError('''No paramsets were passed to experiment. Pass them either when calling experiment or in decorator.
    
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
            self.name, 
            self.version, 
            list(map(lambda e: e[0], self.paramsets))
        )
        state_manager = ExperimentStateManager(self.state)
        state_manager.bootstrap(experiment=self)

        from experiments_utils import settings  # pylint: disable=import-outside-toplevel
        conf.settings = settings
        logging.basicConfig(level=self._logger.level)
        self._initilize_experiment_logger()

        ExperimentContext.__GLOBAL_CONTEXT__ = ExperimentContext(
            name=self.name,
            version=self.version,
            paramsets_names=self.state.paramsets_names,
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
                self._remote_monitor._mark_experiment_as_killed()  # pylint: disable=protected-access
            self._event_emitter.emit_event(ExperimentEndEvent(self.name))
        finally:
            self.results = self._event_handler._results  # pylint: disable=protected-access
            if self._remote_monitor is not None:
                self._remote_monitor.terminate()
            ExperimentContext.__GLOBAL_CONTEXT__ = None
        return self.results

    __call__ = _run


def experiment(
    name: str,
    paramsets: List[Tuple[str, Dict[str, Any]]] = None,
    _file_: str = None,
    n_jobs: int = 4,
    version: str = None,
    plugins: List[Plugin] = [],
):
    """Decorator for experiment functions

    Args:
        name (str): Name of experiment (used for generating results)
        paramsets (List[Tuple[str, Dict[str, Any]]]): list containing sets of parameters for experiment to run with
        _file_ (str) optional __file__ variable from experiment main file. It will be automatically detected.
        max_threads (int) max number of threard, Default 8
        version (str) version string, Default is None
    """
    def wrapper(function):
        experiment_instance = Experiment(
            name=name,
            paramsets=paramsets,
            _file_=_file_,
            n_jobs=n_jobs,
            version=version,

            function=function
        )
        for plugin in plugins:
            experiment_instance.add_plugin(plugin)
        return experiment_instance
    return wrapper
