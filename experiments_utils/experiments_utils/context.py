from __future__ import annotations
from copy import deepcopy
from logging import Logger
from typing import List
from .events.emitter import EventEmitter


class ExperimentContext:
    """Class storing basic information about experiment run context like paramset name
    """
    __GLOBAL_CONTEXT__: ExperimentContext = None
    __EVENT_EMITTER__: EventEmitter = None

    def __init__(
        self,
        name: str,
        paramsets_names: List[str],
        paramset_name: str,
        current_dir: str,
        version: str = None,
        logger: Logger = None
    ) -> None:
        self._name: str = name
        self._version: str = version
        self._paramsets_names: List[str] = paramsets_names
        self._paramset_name: str = paramset_name
        self._current_dir: str = current_dir

        self.logger: Logger = deepcopy(logger)
        self._logs_handlers = logger.handlers

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def paramset_name(self) -> str:
        return self._paramset_name

    @property
    def paramsets_names(self) -> str:
        return self._paramsets_names

    @property
    def current_dir(self) -> str:
        return self._current_dir

    @staticmethod
    def get_instance() -> ExperimentContext:
        return ExperimentContext.__GLOBAL_CONTEXT__
