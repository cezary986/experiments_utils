from __future__ import annotations
from logging import Logger
from typing import Callable, List
from datetime import datetime
import traceback
from .logs import get_step_logger
from . import conf
from .context import ExperimentContext
from .events.emitter import EventEmitter
from .events import StepStartEvent, StepEndEvent, StepErrorEvent, StepSuccessEvent


class Step:
    """Wrapper class for experiment step function"""

    __registered_steps__: List[Step] = []
    __event_emitter__: EventEmitter

    @staticmethod 
    def get_all_registered_steps() -> List[Step]:
        return Step.__registered_steps__

    def __init__(self, function: Callable, name: str) -> None:
        """Constructor. NOTE: Its recomended to use @step function decorator rather
        than using this constructor.
        Args:
            function (Callable): step function to wrap
            name (str): step name - used for logging
        """
        self.function: Callable = function
        self.name: str = name
        self.experiment_name: str = None
        self.paramset_name: str = None
        self.logger: Logger = None
        self._experiment_logger: Logger = None

    def run(self, *args, **kwargs):
        """Run step function"""
        context: ExperimentContext = ExperimentContext.__GLOBAL_CONTEXT__
        event_emitter: EventEmitter = ExperimentContext.__EVENT_EMITTER__
        self.experiment_name = context.name
        self.paramset_name = context.paramset_name
        self.logger = get_step_logger(self.name, self.paramset_name)
        self._experiment_logger = context.logger

        event_emitter.emit_event(StepStartEvent(
            self.experiment_name,
            self.paramset_name,
            self.name
        ))
        event_emitter.emit_event(StepStartEvent(
            self.experiment_name,
            self.paramset_name,
            self.name,
            event_type=f'{self.name}__STEP_START'
        ))
        try:
            start_time = datetime.now(tz=conf.settings.EXPERIMENT_TIMEZONE)
            self.logger.info(f'Started step "{self.name}" for paramset "{self.paramset_name}"')
            self._experiment_logger.info(f'Started step "{self.name}" for paramset "{self.paramset_name}"')
            
            result = self.function(*args, **kwargs)
            
            now = datetime.now(tz=conf.settings.EXPERIMENT_TIMEZONE)
            self.logger.info(f'Finished step "{self.name}" for paramset "{self.paramset_name}". Took: {now - start_time}')
            self._experiment_logger.info(f'Finished step "{self.name}" for paramset "{self.paramset_name}". Took: {now - start_time}')
            
            event_emitter.emit_event(StepSuccessEvent(
                self.experiment_name,
                self.paramset_name,
                self.name
            ))
            event_emitter.emit_event(StepSuccessEvent(
                self.experiment_name,
                self.paramset_name,
                self.name,
                event_type=f'{self.name}__STEP_SUCCESS'
            ))
        except Exception as error:
            now = datetime.now(tz=conf.settings.EXPERIMENT_TIMEZONE)
            self._experiment_logger.info(f'Exception during step "{self.name}" for paramset "{self.paramset_name}". Took: {now - start_time}')
            self.logger.info(f'Exception during step "{self.name}" for paramset "{self.paramset_name}". Took: {now - start_time}')

            self.logger.error(error, exc_info=True)
            stack_trace: str = traceback.format_exc()
            event_emitter.emit_event(StepErrorEvent(
                self.experiment_name,
                error,
                stack_trace,
                self.paramset_name,
                self.name
            ))
            event_emitter.emit_event(StepErrorEvent(
                self.experiment_name,
                error,
                stack_trace,
                self.paramset_name,
                self.name,
                event_type=f'{self.name}__STEP_ERROR'
            ))
            event_emitter.emit_event(StepEndEvent(
                self.experiment_name,
                self.paramset_name,
                self.name
            ))
            event_emitter.emit_event(StepEndEvent(
                self.experiment_name,
                self.paramset_name,
                self.name,
                event_type=f'{self.name}__STEP_END'
            ))
            raise error
        event_emitter.emit_event(StepEndEvent(
            self.experiment_name,
            self.paramset_name,
            self.name
        ))
        event_emitter.emit_event(StepEndEvent(
            self.experiment_name,
            self.paramset_name,
            self.name,
            event_type=f'{self.name}__STEP_END'
        ))
        return result

    __call__ = run


def step(
    name: str = None
):
    """Decorator for experiment step functions

    Args:
        name (str, optional): Optional step name. Defaults is step function name.
    """
    def wrapper(funct: Callable):
        # if step name is not given take function name
        _name = name
        if _name is None:
            _name = funct.__name__
        step = Step(
            name=_name,
            function=funct
        )
        Step.__registered_steps__.append(step)
        return step
    return wrapper
