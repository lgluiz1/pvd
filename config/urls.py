from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('', include('usuarios.urls')),
    path('dashboard/', include('relatorios.urls')),
    path('empresas/', include('empresas.urls')),
    path('produtos/', include('produtos.urls')),
    path('estoque/', include('estoque.urls')),
    path('vendas/', include('vendas.urls')),
    path('caixa/', include('caixa.urls')),
    path('financeiro/', include('financeiro.urls')),
    path('clientes/', include('clientes.urls')),
    path('fornecedores/', include('fornecedores.urls')),
    path('promocoes/', include('promocoes.urls')),
    path('auditoria/', include('auditoria.urls')),
    path('', include('assinaturas.urls')),
    # API
    path('api/', include('core.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
