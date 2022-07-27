from multiprocess.queues import Queue
from .event_types import EventTypes
from .events import ExperimentEvent, ExperimentParamSetEvent, ExperimentStepEvent, _BaseEvent
from typing import Union


class EventEmitter:
    """Class for emitting different experiment events
    """

    def __init__(self, event_queue: Queue) -> None:
        self._event_queue: Queue = event_queue

    def emit_event(
        self,
        event: Union[ExperimentEvent,
                     ExperimentParamSetEvent, ExperimentStepEvent]
    ):
        """Emit event to all listeners.

        Args:
            event (Union[ExperimentEvent, ExperimentParamSetEvent, ExperimentStepEvent]): event
        """
        self._event_queue.put_nowait(event)
