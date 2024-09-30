from clearml import Task
from experiments_utils.plugin import Plugin
from typing import Dict, Any
from experiments_utils.experiment import Experiment
from experiments_utils.context import ExperimentContext
from experiments_utils.events import EventTypes, StepStartEvent


class ClearMLPlugin(Plugin):

    _task: Task = None

    def __init__(self, project_name: str) -> None:
        super().__init__()
        self.project_name: str = project_name

    @property
    def name(self) -> str:
        return 'clearml-plugin'

    @property
    def description(self) -> str:
        return 'Plugin for ClearML integration.'

    @property
    def version(self) -> str:
        return '1.0.1'

    @property
    def task(self) -> Task:
        return self._task

    def experiment_initialize(self, experiment: Experiment):

        @experiment.on_event(EventTypes.STEP_START)
        def _(event: StepStartEvent):
            paramset_task = Task.get_task(
                task_name=event.paramset_name, project_name=self.project_name
            )
            paramset_task.set_tags([event.step_name])

    def paramset_start(self, context: ExperimentContext, params: Dict[str, Any]):
        self._task = Task.init(
            project_name=self.project_name,
            task_name=context.paramset_name
        )
        self.task.connect_configuration(params, name='Parameters')

    def paramset_finish(self, context: ExperimentContext, error: Exception = None):
        if error is None:
            self.task.mark_completed()
        elif isinstance(error, KeyboardInterrupt):
            self.task.mark_stopped()
        else:
            self.task.mark_failed()
        self.task.flush(True)
        self.task.close()
