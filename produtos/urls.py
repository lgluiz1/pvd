from django.urls import path
from produtos import views

app_name = 'produtos'

urlpatterns = [
    path('', views.produto_lista, name='lista'),
    path('criar/', views.produto_criar, name='criar'),
    path('<uuid:pk>/', views.produto_detalhe, name='detalhe'),
    path('<uuid:pk>/editar/', views.produto_editar, name='editar'),
    path('categorias/', views.categoria_lista, name='categorias'),
    path('embalagens/', views.embalagem_lista, name='embalagens'),
    path('buscar-codigo/', views.buscar_por_codigo, name='buscar_codigo'),
    path('entrada-estoque/', views.entrada_estoque, name='entrada_estoque'),
]
