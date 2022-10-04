import sys
from argparse import ArgumentError
from typing import Union
from .context import ExperimentContext
from .experiment import Experiment
from .step import Step
from logging import Logger


def get_logger(experiment_or_step: Union[Experiment, Step]) -> Logger:
    """Return logger object for given experiment of step

    Args:
        experiment_or_step (Union[Experiment, Step]): Experiment or Step function

    Raises:
        ArgumentError: if passed argument is neither Experiment not Step object.

    Returns:
        Logger: logger object
    """
    if isinstance(experiment_or_step, Experiment):
        logger = ExperimentContext.__GLOBAL_CONTEXT__.logger
        return logger
    elif isinstance(experiment_or_step, Step):
        return experiment_or_step.logger
    else:
        raise ArgumentError(experiment_or_step, 'Value should be either Experiment or Step instance')
