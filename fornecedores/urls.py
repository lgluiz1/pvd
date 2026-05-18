from django.urls import path
from fornecedores import views
app_name = 'fornecedores'
urlpatterns = [
    path('', views.fornecedor_lista, name='lista'),
    path('criar/', views.fornecedor_criar, name='criar'),
    path('<uuid:pk>/editar/', views.fornecedor_editar, name='editar'),
]
