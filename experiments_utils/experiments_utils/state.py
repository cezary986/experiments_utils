from enum import Enum
from typing import Dict, List
from datetime import datetime
from .events import *
from .step import Step


class States(Enum):
    NONE: str = 'NONE'
    FAILED: str = 'FAILED'
    KILLED: str = 'KILLED'
    RUNNING: str = 'RUNNING'
    SUCCESSFUL: str = 'SUCCESSFUL'


class StepState:
    """Class allowing to read experiment step execution state.
    """

    def __init__(self, name: str) -> None:
        self._name: str = name
        self._state: States = States.NONE
        self._started: datetime = None
        self._finished: datetime = None
        self._error: Exception = None
        self._error_stack_trace: str = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> States:
        return self._state

    @property
    def started(self) -> datetime:
        return self._started

    @property
    def finished(self) -> datetime:
        return self._finished

    @property
    def error(self) -> datetime:
        return self._error

    @property
    def error_stack_trace(self) -> datetime:
        return self._error_stack_trace

    def to_json(self) -> dict:
        return {
            'name': self.name,
            'state': self.state.value,
            'started': str(self.started) if self.started is not None else None,
            'finished': str(self.finished) if self.finished is not None else None,
            'started_ts': self.started.timestamp() if self.started is not None else None,
            'finished_ts': self.finished.timestamp() if self.finished is not None else None,
            'error': {
                'message': self.error,
                'stack_trace': self.error_stack_trace,
            } if self.error is not None else None
        }


class ParamSetState:
    """Class allowing to read experiment paramset execution state.
    """

    def __init__(self, name: str) -> None:
        self._name: str = name
        self._started: datetime = None
        self._finished: datetime = None
        self._steps_names: List[str] = list(
            map(lambda s: s.name, Step.get_all_registered_steps()))
        self._steps_state: Dict[str, StepState] = {
            name: StepState(name) for name in self._steps_names
        }
        self._error: Exception = None
        self._error_stack_trace: str = None
        self._state: States = States.NONE
        self.current_step: str = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def steps_names(self) -> List[str]:
        return self._steps_names

    @property
    def state(self) -> StepState:
        return self._state

    @property
    def started(self) -> datetime:
        return self._started

    @property
    def finished(self) -> datetime:
        return self._finished

    @property
    def error(self) -> datetime:
        return self._error

    @property
    def error_stack_trace(self) -> datetime:
        return self._error_stack_trace

    def get_step_state(self, step_name: str) -> StepState:
        return self._steps_state[step_name]

    def to_json(self) -> dict:
        return {
            'paramset_name': self.name,
            'state': self.state.value,
            'started': str(self.started) if self.started is not None else None,
            'finished': str(self.finished) if self.finished is not None else None,
            'started_ts': self.started.timestamp() if self.started is not None else None,
            'finished_ts': self.finished.timestamp() if self.finished is not None else None,
            'error': {
                'message': self.error,
                'stack_trace': self.error_stack_trace,
            } if self.error is not None else None,
            "steps": {
                name: step_state.to_json() for name, step_state in self._steps_state.items()
            }
        }


class ExperimentState:
    """Class allowing to read current experiment execution state.
    """

    def __init__(
        self,
        experiment_name: str,
        experiment_version: str,
        paramsets_names: List[str]
    ) -> None:
        self._experiment_name: str = experiment_name
        self._experiment_version: str = experiment_version
        self._paramsets_names: str = paramsets_names
        self._started: datetime = None
        self._finished: datetime = None
        self._state: States = States.NONE
        self._errors: List[Exception] = []
        self._errors_stack_traces: List[str] = []
        self._steps_names: List[str] = list(
            map(lambda s: s.name, Step.get_all_registered_steps()))
        self._paramsets_state: Dict[str, ParamSetState] = {
            name: ParamSetState(name) for name in paramsets_names
        }
        self._running_paramsets: List[str] = []
        self._failed_paramsets: List[str] = []
        self._finished_paramsets: List[str] = []

    @property
    def experiment_name(self) -> str:
        return self._experiment_name

    @property
    def experiment_version(self) -> str:
        return self._experiment_version

    @property
    def state(self) -> States:
        return self._state

    @property
    def paramsets_names(self) -> List[str]:
        return self._paramsets_names

    @property
    def started(self) -> datetime:
        return self._started

    @property
    def finished(self) -> datetime:
        return self._finished

    @property
    def errors(self) -> List[Exception]:
        return self._errors

    @property
    def errors_stack_traces(self) -> List[str]:
        return self._errors_stack_traces

    @property
    def steps_names(self) -> List[str]:
        return self._steps_names

    @property
    def running_paramsets(self) -> List[str]:
        return self._running_paramsets

    @property
    def failed_paramsets(self) -> List[str]:
        return self._failed_paramsets

    @property
    def finished_paramsets(self) -> List[str]:
        return self._finished_paramsets

    def get_paramset_state(self, paramset_name: str) -> ParamSetState:
        return self._paramsets_state[paramset_name]

    def to_json(self) -> dict:
        return {
            'experiment_name': self.experiment_name,
            'experiment_version': self.experiment_version,
            'state': self.state.value,
            'started': str(self.started) if self.started is not None else None,
            'finished': str(self.finished) if self.finished is not None else None,
            'started_ts': self.started.timestamp() if self.started is not None else None,
            'finished_ts': self.finished.timestamp() if self.finished is not None else None,
            "steps": self.steps_names,
            'errors': [
                {
                    'message': self.errors[i],
                    'stack_trace': self.errors_stack_traces[i],
                } for i in range(0, len(self.errors))
            ],
            'paramsets': {
                name: paramset_state.to_json() for name, paramset_state in self._paramsets_state.items()
            }
        }


class ExperimentStateManager:

    def __init__(self, state: ExperimentState):
        self._state: ExperimentState = state

    def bootstrap(self, experiment):
        @experiment.on_event(EventTypes.EXPERIMENT_START)
        def _(event: ExperimentStartEvent):
            self._state._started = event.timestamp
            self._state._state = States.RUNNING

        @experiment.on_event(EventTypes.EXPERIMENT_SUCCESS)
        def _(event: ExperimentEndEvent):
            self._state._finished = event.timestamp
            self._state._state = States.SUCCESSFUL

        @experiment.on_event(EventTypes.EXPERIMENT_SUCCESS)
        def _(event: ExperimentEndEvent):
            self._state._finished = event.timestamp
            self._state._state = States.SUCCESSFUL

        @experiment.on_event(EventTypes.EXPERIMENT_PARAMSET_START)
        def _(event: ParamsetEndEvent):
            self._state.get_paramset_state(
                event.paramset_name)._started = event.timestamp
            self._state.get_paramset_state(
                event.paramset_name)._state = States.RUNNING
            self._state._running_paramsets.append(event.paramset_name)

        @experiment.on_event(EventTypes.EXPERIMENT_PARAMSET_SUCCESS)
        def _(event: ParamsetEndEvent):
            self._state.get_paramset_state(
                event.paramset_name)._finished = event.timestamp
            self._state.get_paramset_state(
                event.paramset_name)._state = States.SUCCESSFUL
            if event.paramset_name in self._state._running_paramsets:
                self._state._running_paramsets.remove(event.paramset_name)
            self._state._finished_paramsets.append(event.paramset_name)

        @experiment.on_event(EventTypes.EXPERIMENT_PARAMSET_ERROR)
        def _(event: ParamsetErrorEvent):
            paramset_state: ParamSetState = self._state.get_paramset_state(
                event.paramset_name)
            paramset_state._error = event.exception
            paramset_state._error_stack_trace = event.stack_trace
            paramset_state._finished = event.timestamp
            paramset_state._state = States.FAILED
            if event.paramset_name in self._state._running_paramsets:
                self._state._running_paramsets.remove(event.paramset_name)
            self._state._failed_paramsets.append(event.paramset_name)

        @experiment.on_event(EventTypes.STEP_START)
        def _(event: StepEndEvent):
            self._state.get_paramset_state(
                event.paramset_name).current_step = event.step_name
            step_state: StepState = self._state.get_paramset_state(
                event.paramset_name).get_step_state(event.step_name)

            step_state._started = event.timestamp
            step_state._state = States.RUNNING

        @experiment.on_event(EventTypes.STEP_ERROR)
        def _(event: StepErrorEvent):
            step_state: StepState = self._state.get_paramset_state(
                event.paramset_name).get_step_state(event.step_name)
            step_state._error = event.exception
            step_state._error_stack_trace = event.stack_trace
            step_state._finished = event.timestamp
            step_state._state = States.FAILED

        @experiment.on_event(EventTypes.STEP_SUCCESS)
        def _(event: StepEndEvent):
            step_state: StepState = self._state.get_paramset_state(
                event.paramset_name).get_step_state(event.step_name)
            step_state._finished = event.timestamp
            step_state._state = States.SUCCESSFUL
