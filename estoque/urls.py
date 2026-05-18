from django.urls import path
from estoque import views

app_name = 'estoque'

urlpatterns = [
    path('', views.estoque_lista, name='lista'),
    path('movimentar/', views.estoque_movimentar, name='movimentar'),
    path('historico/<uuid:produto_id>/', views.estoque_historico, name='historico'),
    path('alertas/', views.estoque_alertas, name='alertas'),
]
