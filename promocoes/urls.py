from django.urls import path
from promocoes import views
app_name = 'promocoes'
urlpatterns = [
    path('', views.promocao_lista, name='lista'),
    path('criar/', views.promocao_criar, name='criar'),
    path('<uuid:pk>/toggle/', views.promocao_toggle, name='toggle'),
]
