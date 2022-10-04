from datetime import datetime
from typing import Any
from .event_types import EventTypes
from .. import conf


class _BaseEvent:

    def __init__(self, event_type: str) -> None:
        self._timestamp: datetime = datetime.now(
            tz=conf.settings.EXPERIMENT_TIMEZONE)
        self._event_type: str = event_type

    @property
    def event_type(self) -> str:
        return self._event_type

    @property
    def timestamp(self) -> datetime:
        return self._timestamp


class ErrorEvent:
    """Base class for error events
    """

    def __init__(self, exception: Exception, stack_trace: str) -> None:
        self._exception: Exception = exception
        self._stack_trace: str = stack_trace

    @property
    def exception(self) -> Exception:
        return self._exception

    @property
    def stack_trace(self) -> Exception:
        return self._stack_trace


class ExperimentEvent(_BaseEvent):
    """Base class for experiment events
    """

    def __init__(
        self,
        event_type,
        experiment_name: str,
    ) -> None:
        super().__init__(event_type)
        self._experiment_name: str = experiment_name

    @property
    def experiment_name(self) -> str:
        return self._experiment_name


class ExperimentParamSetEvent(ExperimentEvent):
    """Base class for events connected with given experiment paramset
    """

    def __init__(
        self,
        event_type: str,
        experiment_name: str,
        paramset_name: str,
    ) -> None:
        super().__init__(event_type, experiment_name)
        self._paramset_name: str = paramset_name

    @property
    def paramset_name(self) -> str:
        return self._paramset_name


class ExperimentStepEvent(ExperimentParamSetEvent):
    """Base class for events connected with given experiment step and paramset
    """

    def __init__(
        self,
        event_type: str,
        experiment_name: str,
        paramset_name: str,
        step_name: str
    ) -> None:
        super().__init__(event_type, experiment_name, paramset_name)
        self._step_name: str = step_name

    @property
    def step_name(self) -> str:
        return self._step_name

# ==========================================================================
# ==========================================================================


class ExperimentStartEvent(ExperimentEvent):

    def __init__(
            self,
            experiment_name: str,
            event_type: str = EventTypes.EXPERIMENT_START.value
    ) -> None:
        super().__init__(event_type, experiment_name)


class ExperimentEndEvent(ExperimentEvent):

    def __init__(
        self,
        experiment_name: str,
        event_type: str = EventTypes.EXPERIMENT_END.value
    ) -> None:
        super().__init__(event_type, experiment_name)


class ExperimentSuccessEvent(ExperimentEvent):

    def __init__(
        self,
        experiment_name: str,
        event_type: str = EventTypes.EXPERIMENT_SUCCESS.value
    ) -> None:
        super().__init__(event_type, experiment_name)


class ParamsetStartEvent(ExperimentParamSetEvent):

    def __init__(
        self,
        experiment_name: str,
        paramset_name: str,
        event_type: str = EventTypes.EXPERIMENT_PARAMSET_START.value
    ) -> None:
        super().__init__(event_type, experiment_name, paramset_name)


class ParamsetEndEvent(ExperimentParamSetEvent):

    def __init__(
        self,
        experiment_name: str,
        paramset_name: str,
        event_type: str = EventTypes.EXPERIMENT_PARAMSET_END.value
    ) -> None:
        super().__init__(event_type,
                         experiment_name, paramset_name)


class ParamsetSuccessEvent(ExperimentParamSetEvent):

    def __init__(
        self,
        experiment_name: str,
        paramset_name: str,
        event_type: str = EventTypes.EXPERIMENT_PARAMSET_SUCCESS.value,
        result: Any = None
    ) -> None:
        super().__init__(event_type,
                         experiment_name, paramset_name)
        self.result: Any = result


class ParamsetErrorEvent(ExperimentParamSetEvent, ErrorEvent):

    def __init__(
        self,
        experiment_name: str,
        exception: Exception,
        stack_trace: str,
        paramset_name: str,
        event_type: str = EventTypes.EXPERIMENT_PARAMSET_ERROR.value
    ) -> None:
        ExperimentParamSetEvent.__init__(
            self, event_type, experiment_name, paramset_name)
        ErrorEvent.__init__(self, exception, stack_trace)


class StepStartEvent(ExperimentStepEvent):

    def __init__(
        self,
        experiment_name: str,
        paramset_name: str,
        step_name: str,
        event_type: str = EventTypes.STEP_START.value
    ) -> None:
        super().__init__(event_type, experiment_name,
                         paramset_name, step_name)


class StepEndEvent(ExperimentStepEvent):

    def __init__(
        self,
        experiment_name: str,
        paramset_name: str,
        step_name: str,
        event_type: str = EventTypes.STEP_END.value
    ) -> None:
        super().__init__(event_type, experiment_name,
                         paramset_name, step_name)


class StepSuccessEvent(ExperimentStepEvent):

    def __init__(
        self,
        experiment_name: str,
        paramset_name: str,
        step_name: str,
        event_type: str = EventTypes.STEP_SUCCESS.value
    ) -> None:
        super().__init__(event_type, experiment_name,
                         paramset_name, step_name)


class StepErrorEvent(ExperimentStepEvent, ErrorEvent):

    def __init__(
        self,
        experiment_name: str,
        exception: Exception,
        stack_trace: str,
        paramset_name: str,
        step_name: str,
        event_type: str = EventTypes.STEP_ERROR.value
    ) -> None:
        ExperimentStepEvent.__init__(
            self, event_type, experiment_name, paramset_name, step_name)
        ErrorEvent.__init__(self, exception, stack_trace)
