from django.urls import path
from financeiro import views
app_name = 'financeiro'
urlpatterns = [
    path('', views.fiado_lista, name='lista'),
    path('criar/', views.fiado_criar, name='criar'),
    path('<uuid:pk>/', views.fiado_detalhe, name='detalhe'),
    path('pagar/<uuid:parcela_id>/', views.fiado_pagar, name='pagar'),
]
