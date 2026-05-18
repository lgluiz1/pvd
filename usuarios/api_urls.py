from django.urls import path
from usuarios import api_views

urlpatterns = [
    path('login/', api_views.api_login, name='api_login'),
    path('me/', api_views.api_me, name='api_me'),
]
