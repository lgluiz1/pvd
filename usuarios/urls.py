from django.urls import path
from usuarios import views

app_name = 'usuarios'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('usuarios/', views.usuario_lista, name='lista'),
    path('usuarios/criar/', views.usuario_criar, name='criar'),
    path('usuarios/<uuid:pk>/editar/', views.usuario_editar, name='editar'),
]
