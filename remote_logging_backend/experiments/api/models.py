from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class CustomUser(AbstractUser):
    cash = models.FloatField(editable=True, null=False, default=0.0)

    def __str__(self):
        return self.username


class Experiment(models.Model):
    name = models.CharField(max_length=200, null=False, unique=True)
    description = models.TextField(null=True, blank=True)
    last_run = models.ForeignKey(
        'api.ExperimentRun',
        default=None,
        related_name='experiment_last_run',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    is_running = models.BooleanField(default=False, null=False, blank=True)

    def __str__(self) -> str:
        return f'{self.name}'


class ExperimentRun(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    started = models.DateTimeField(editable=False, blank=True)
    finished = models.DateTimeField(null=True)
    killed = models.BooleanField(default=False, blank=True)
    has_errors = models.BooleanField(default=False, null=False, blank=True)
    number_of_configs = models.IntegerField(default=-1)
    finished_configs = models.IntegerField(default=0)
    configs_execution = models.JSONField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.started = timezone.now()
        return super(ExperimentRun, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return f'"{self.experiment.name}" started {self.started.strftime("%d.%m.%Y_%H.%M.%S")}'


class ExperimentConfigRun(models.Model):
    run = models.ForeignKey(ExperimentRun, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=False, unique=True)
    started = models.DateTimeField()
    finished = models.DateTimeField(null=True)
    has_errors = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'"{self.run.experiment.name}" config "{self.name}" started {self.started.strftime("%d.%m.%Y_%H.%M.%S")}'


class LogEntry(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    experiment_run = models.ForeignKey(ExperimentRun, on_delete=models.CASCADE)
    # experiment_config_run = models.ForeignKey(ExperimentConfigRun, on_delete=models.CASCADE, null=True)

    timestamp_string = models.CharField(max_length=200, null=False)
    timestamp = models.DateTimeField()
    logger = models.CharField(max_length=200, null=True)
    config_name = models.CharField(
        max_length=200, null=True, default=None, blank=True)
    step_name = models.CharField(
        max_length=200, null=True, default=None, blank=True)
    filename = models.CharField(max_length=200, null=True)
    function_name = models.CharField(max_length=200, null=True)
    line_number = models.IntegerField(default=-1, null=True)
    level = models.CharField(max_length=30, null=False)
    level_value = models.IntegerField(null=False)
    stack_info = models.TextField(null=True)
    message = models.TextField(null=False)

    def __str__(self) -> str:
        return f'[{self.level}] {self.experiment.name}.{self.config_name}: "{self.message}"'
