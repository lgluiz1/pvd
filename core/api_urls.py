from django.urls import path, include

# API Router principal - agrupa todas as APIs
urlpatterns = [
    path('empresas/', include('empresas.api_urls')),
    path('produtos/', include('produtos.api_urls')),
    path('estoque/', include('estoque.api_urls')),
    path('vendas/', include('vendas.api_urls')),
    path('caixa/', include('caixa.api_urls')),
    path('financeiro/', include('financeiro.api_urls')),
    path('clientes/', include('clientes.api_urls')),
    path('fornecedores/', include('fornecedores.api_urls')),
    path('promocoes/', include('promocoes.api_urls')),
    path('sync/', include('sync.api_urls')),
    path('auth/', include('usuarios.api_urls')),
]
