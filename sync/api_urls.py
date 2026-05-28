from django.urls import path
from sync import api_views
urlpatterns = [
    path('snapshot/', api_views.sync_snapshot, name='snapshot'),
    path('upload/', api_views.sync_upload, name='upload'),
    path('mp-config/', api_views.sync_mp_config, name='mp_config'),
]
