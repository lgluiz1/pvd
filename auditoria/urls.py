from django.urls import path
from auditoria import views
app_name = 'auditoria'
urlpatterns = [
    path('', views.auditoria_lista, name='lista'),
]
