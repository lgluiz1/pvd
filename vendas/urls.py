from django.urls import path
from vendas import views

app_name = 'vendas'

urlpatterns = [
    path('', views.venda_lista, name='lista'),
    path('<uuid:pk>/', views.venda_detalhe, name='detalhe'),
    path('<uuid:pk>/cancelar/', views.venda_cancelar, name='cancelar'),
    path('criar-api/', views.venda_criar_api, name='criar_api'),
]
