from django.urls import path
from clientes import views
app_name = 'clientes'
urlpatterns = [
    path('', views.cliente_lista, name='lista'),
    path('criar/', views.cliente_criar, name='criar'),
    path('buscar-nfc/', views.buscar_cliente_nfc, name='buscar_nfc'),
    path('<uuid:pk>/editar/', views.cliente_editar, name='editar'),
]
