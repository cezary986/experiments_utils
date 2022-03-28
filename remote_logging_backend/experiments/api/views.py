import json
import sys
import os
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, render
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework import status
from api.serializers import *
from api.models import *
from django.http.response import JsonResponse
from django.contrib import auth
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from api.notifications import send_notification
from api import __version__
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{dir_path}/../scrappers')
User = get_user_model()


class VersionView(APIView):

    authentication_classes = []

    def get(self, request):
        return JsonResponse({'version': __version__}, status=200)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    pagination_class = None
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']


class CurrentUserView(APIView):
    authentication_classes = [TokenAuthentication, BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return JsonResponse(UserSerializer(request.user, context={'request': request}).data, status=200)


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    pagination_class = None
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, BasicAuthentication]
    http_method_names = ['get']


class LoginView(APIView):

    authentication_classes = []

    def post(self, request):
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            username = body['username']
            password = body['password']
        except KeyError:
            return JsonResponse({'message': 'No username or password field'}, status=status.HTTP_400_BAD_REQUEST)

        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return JsonResponse({
                'token': token.key
            }, status=200)
        else:
            return JsonResponse({'message': 'Invalid login or password'}, status=401)


class LogoutView(APIView):

    authentication_classes = []

    def post(self, request):
        if request.user.is_authenticated:
            token, created = Token.objects.get_or_create(user=request.user)
            token.delete()
            auth.logout(request)
            return JsonResponse({'message': 'Logged out'}, status=200)
        else:
            return JsonResponse({'message': 'Already logged out'}, status=200)

class ExperimentsRunViewSet(viewsets.ViewSet):
    pagination_class = None
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, BasicAuthentication]

    def destroy(self, request, pk):
        run: ExperimentRun = get_object_or_404(
            ExperimentRun, pk=pk)
        run.delete()
        return JsonResponse({'message': 'deleted'}, status=200)

    def retrieve(self, request, pk):
        run: ExperimentRun = get_object_or_404(
            ExperimentRun.objects, pk=pk)
        serializer = ExperimentRunSerializer(run, context={'request': request})
        return JsonResponse(serializer.data, safe=False)

    def list(self, request):
        experiment_name = request.GET.get('experiment_name', None)
        runs = ExperimentRun.objects.all().order_by('-started')
        if experiment_name is not None:
            runs = ExperimentRun.objects.filter(
                experiment__name=experiment_name).order_by('-started')
        serializer = ExperimentRunSerializer(
            runs, many=True, context={'request': request})
        return JsonResponse(serializer.data, safe=False)

    def create(self, request, **kwargs):
        request_json = request.data
        experiment_name = request_json.get('experiment_name', None)
        if experiment_name is None:
            return JsonResponse({'message': "No 'experiment_name' value specified. Send valid experiment name in body to bind run with experiment instance."}, status=status.HTTP_400_BAD_REQUEST)
        experiment: Experiment = get_object_or_404(
            Experiment, name=experiment_name)

        run = ExperimentRun.objects.create(
            experiment=experiment,
            number_of_configs=request_json.get('number_of_configs', -1)
        )
        experiment.last_run = run
        experiment.save()
        return JsonResponse({'run_id': run.id})

    def partial_update(self, request, pk=None):
        run: ExperimentRun = get_object_or_404(
            ExperimentRun, pk=pk)
        request_json = request.data
        for value in request_json['configs_execution'].values():
            if value['has_errors']:
                run.has_errors = True
                break
        run.finished = request_json.get('finished', None)
        run.killed = request_json.get('killed', run.killed)
        run.finished_configs = request_json.get(
            'finished_configs', run.finished_configs)
        run.configs_execution = request_json['configs_execution']
        run.save()
        if request_json.get('has_errors', False):
            print('SEND')
            send_notification(
                title=f'Error in experiment "{run.experiment.name}"',
                message=f'Error during experiment execution'
            )
        return JsonResponse({'message': "updated"}, safe=False, status=status.HTTP_200_OK)


class ExperimentsViewSet(viewsets.ModelViewSet):

    def get_serializer_class(self):
        if self.action == 'create':
            return ExperimentCreateSerializer
        else:
            return ExperimentSerializer

    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, BasicAuthentication]
    http_method_names = ['get', 'post', 'delete']
    pagination_class = None


LOGS_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'WARN': 30,
    'ERROR': 40,
}


class LogEntryViewSet(viewsets.ViewSet):

    http_method_names = ['get', 'post', 'delete']
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, BasicAuthentication]
    pagination_class = LimitOffsetPagination

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.paginator = LimitOffsetPagination()
        self.paginator.default_limit = 2

    def get_serializer_class(self):
        if self.action == 'create':
            return LogEntryCreateSerializer
        else:
            return LogEntrySerializer

    def list(self, request, run_id: int):
        run: ExperimentRun = get_object_or_404(ExperimentRun, pk=run_id)
        url_params: dict = request.GET
        filters = {}
        if 'level' in url_params:
            filters['level_value__gte'] = LOGS_LEVELS[url_params['level']]
        logs = LogEntry.objects.filter(experiment_run__id=run.id, **filters).order_by('-timestamp')
        page = self.paginator.paginate_queryset(logs, request)
        serializer = LogEntrySerializer(
            page, many=True, context={'request': request})
        return self.paginator.get_paginated_response(serializer.data)

    def create(self, request, run_id: int):
        run: ExperimentRun = get_object_or_404(ExperimentRun, pk=run_id)

        serializer = LogEntryCreateSerializer(data=request.data, many=True)
        if serializer.is_valid():
            data = serializer.validated_data
            for log in data:
                LogEntry.objects.create(
                    **log,
                    experiment=run.experiment,
                    experiment_run=run
                )
            return JsonResponse({'message': f'Saved {len(data)} log entries'})
        else:
            print(serializer.error_messages)
            return JsonResponse({
                'message': f'Failed to save logs, invalid body',
                'request_body': request.data,
                'errors': [str(error) for error in serializer.errors]
            }, status=status.HTTP_400_BAD_REQUEST)
