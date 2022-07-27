from enum import Enum


class EventTypes(Enum):
    """Enum containing available event types

    `EXPERIMENT_START` - event trigger on experiment run start
    `EXPERIMENT_END` - event trigger on experiment run end
    `EXPERIMENT_FINISHED` - event trigger on experiment finish - no mater if it succeeded or failed 

    `EXPERIMENT_PARAMSET_START` - event trigger on experiment run start with given paramset
    `EXPERIMENT_PARAMSET_END` - event trigger on experiment run end with given paramset
    `EXPERIMENT_PARAMSET_ERROR` - event trigger on experiment error running given paramset

    `STEP_START` - event trigger on experiment's step start
    `STEP_END` - event trigger on experiment's step end
    `STEP_ERROR` - event trigger on experiment's step error

    `REMOTE_LOGGING_FLUSH` - event trigger when remote logging message queue is flushed and logs are send to server

    Event types for every experiment paramset and step are automaticly created and triggered
    on runtime in following notation:
        - `${step_name}__STEP_START`
        - `${step_name}__STEP_END`
        - `${step_name}__STEP_ERROR`
        - `${paramset_name}___PARAMSET_START`
        - `${paramset_name}___PARAMSET_END`
        - `${paramset_name}___PARAMSET_ERROR`
    """
    EXPERIMENT_START: str = 'EXPERIMENT_START'
    EXPERIMENT_SUCCESS: str = 'EXPERIMENT_SUCCESS'
    EXPERIMENT_END: str = 'EXPERIMENT_END'

    EXPERIMENT_PARAMSET_START: str = 'EXPERIMENT_PARAMSET_START'
    EXPERIMENT_PARAMSET_END: str = 'EXPERIMENT_PARAMSET_END'
    EXPERIMENT_PARAMSET_SUCCESS: str = 'EXPERIMENT_PARAMSET_SUCCESS'
    EXPERIMENT_PARAMSET_ERROR: str = 'EXPERIMENT_PARAMSET_ERROR'

    STEP_START: str = 'STEP_START'
    STEP_SUCCESS: str = 'STEP_SUCCESS'
    STEP_END: str = 'STEP_END'
    STEP_ERROR: str = 'STEP_ERROR'

    REMOTE_LOGGING_FLUSH: str = 'REMOTE_LOGGING_FLUSH'
