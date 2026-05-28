from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from assinaturas.webhook_views import efi_notification_webhook

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
    # Webhook Efi (notificacao de pagamento)
    path('api/efi/webhook/', efi_notification_webhook, name='efi_webhook'),
    # API
    path('api/', include('core.api_urls')),
    
    # PWA Service Worker
    path('sw.js', TemplateView.as_view(template_name='sw.js', content_type='application/javascript'), name='sw.js'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
