from django.urls import path
from relatorios import views
app_name = 'relatorios'
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]
