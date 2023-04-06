from __future__ import annotations
import copy
from logging import Logger
from abc import ABC, abstractproperty
import logging
from typing import Any, Dict


class Plugin:

    logger: Logger

    @property
    def name(self) -> str:
        ...

    @property
    def description(self) -> str:
        ...

    @property
    def version(self) -> str:
        ...

    def experiment_initialize(self, experiment):
        ...

    def experiment_finish(self, experiment):
        ...

    def paramset_start(self, context, params: Dict[str, Any]):
        ...

    def paramset_finish(self, context, error: Exception = None):
        ...

    def clone(self) -> Plugin:
        clone = copy.deepcopy(self)
        clone.logger = copy.deepcopy(self.logger)
        return clone
