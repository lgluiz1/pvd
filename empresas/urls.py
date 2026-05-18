from django.urls import path
from empresas import views

app_name = 'empresas'

urlpatterns = [
    path('config/', views.empresa_config, name='config'),
    path('terminal/criar/', views.terminal_criar, name='terminal_criar'),
    path('terminal/<uuid:pk>/toggle/', views.terminal_toggle, name='terminal_toggle'),
]
