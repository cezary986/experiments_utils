from django.urls import include, path
from rest_framework import routers
from api.views import *

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'experiments', ExperimentsViewSet)
router.register(r'experiments_runs', ExperimentsRunViewSet, basename='runs')
router.register(r'logs/(?P<run_id>.+)', LogEntryViewSet, basename='logs')


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    path('version', VersionView.as_view(), name='version'),
    path('user', CurrentUserView.as_view(), name='current_user'),
    path('auth/login', LoginView.as_view(), name='login'),
    path('auth/logout', LogoutView.as_view(), name='logout'),
    path('auth-api/', include('rest_framework.urls', namespace='rest_framework'))
]
