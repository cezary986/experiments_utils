from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from rest_framework import serializers
from api.models import *
User = get_user_model()


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'id', 'username', 'email', 'groups', 'cash']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'id', 'name']


class ExperimentCreateSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Experiment
        fields = [
            'url',
            'id',
            'name',
            'description',
        ]


class ExperimentSerializer(serializers.HyperlinkedModelSerializer):

    class ExperimentRunSimplifiedSerializer(serializers.HyperlinkedModelSerializer):
        class Meta:
            model = ExperimentRun
            fields = [
                'id',
                'started',
                'finished',
                'finished_configs',
                'number_of_configs',
                'has_errors'
            ]

    last_run = ExperimentRunSimplifiedSerializer(many=False)

    class Meta:
        model = Experiment
        fields = [
            'url',
            'id',
            'name',
            'description',
            'last_run',
        ]


class ExperimentRunSerializer(serializers.ModelSerializer):

    configs_execution = serializers.JSONField()

    class Meta:
        model = ExperimentRun
        fields = [
            'id',
            'started',
            'finished',
            'has_errors',
            'finished_configs',
            'number_of_configs',
            'configs_execution'
        ]


class LogEntryCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = LogEntry
        fields = [
            'id',
            'timestamp_string',
            'timestamp',
            'logger',
            'config_name',
            'filename',
            'function_name',
            'line_number',
            'level',
            'level_value',
            'stack_info',
            'message',
        ]


class LogEntrySerializer(serializers.ModelSerializer):

    class Meta:
        model = LogEntry
        fields = [
            'id',
            'timestamp_string',
            'timestamp',
            'logger',
            'config_name',
            'filename',
            'function_name',
            'line_number',
            'level',
            'level_value',
            'stack_info',
            'message',
        ]
