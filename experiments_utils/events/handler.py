from multiprocess.queues import Queue
from .event_types import EventTypes
from .events import _BaseEvent, ExperimentEndEvent, ExperimentSuccessEvent
from typing import Any, Callable, Dict, List, Union


class EventHandler:

    def __init__(self) -> None:
        self._event_queue: Queue = None
        self._event_listeners: Dict[str, List[Callable]] = {
            event_type.value: [] for event_type in EventTypes
        }

    @property
    def event_queue(self):
        return self._event_queue

    @event_queue.setter
    def event_queue(self, queue: Queue):
        self._event_queue = queue

    def add_event_listener(self, event_type: Union[str, EventTypes], handler: Callable[[_BaseEvent], None]):
        """Adds event listener

        Args:
            event_type (EventTypes): event type
            handler (Callable): listener handler function
        """
        if isinstance(event_type, EventTypes):
            event_type = event_type.value
        if event_type not in self._event_listeners:
            self._event_listeners[event_type] = []
        self._event_listeners[event_type].append(handler)

    def on_event(self, event_type: EventTypes):
        """Helper decorator to adding event listeners.

        Args:
            event_type (EventTypes): event type to listen for
        """
        def wrapper(function):
            self.add_event_listener(event_type, handler=function)
            return function
        return wrapper

    def _handle_event(self, event: _BaseEvent = []):
        for listener in self._event_listeners.get(event.event_type, []):
            listener(event)
        for listener in self._event_listeners.get('*', []):
            listener(event)

    def start_listening_for_events(self, paramsets_count: int):
        finished_paramsets_counter: int = 0
        was_error: bool = False
        experiment_name: str = None
        while finished_paramsets_counter < paramsets_count:
            event: _BaseEvent = self._event_queue.get()
            experiment_name = event.experiment_name
            self._handle_event(event)
            if event.event_type == EventTypes.EXPERIMENT_PARAMSET_END.value:
                finished_paramsets_counter += 1
            if event.event_type == EventTypes.EXPERIMENT_PARAMSET_ERROR.value:
                was_error = True
        if not was_error:
            self._handle_event(ExperimentSuccessEvent(experiment_name))
        self._handle_event(ExperimentEndEvent(experiment_name))
