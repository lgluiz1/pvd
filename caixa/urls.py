from django.urls import path
from caixa import views

app_name = 'caixa'

urlpatterns = [
    path('', views.caixa_lista, name='lista'),
    path('abrir/', views.caixa_abrir, name='abrir'),
    path('<uuid:pk>/', views.caixa_detalhe, name='detalhe'),
    path('<uuid:pk>/fechar/', views.caixa_fechar, name='fechar'),
    path('<uuid:pk>/sangria/', views.caixa_sangria, name='sangria'),
    path('<uuid:pk>/suprimento/', views.caixa_suprimento, name='suprimento'),
]
