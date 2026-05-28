from django.urls import path
from local_pdv import views

urlpatterns = [
    path('', views.caixa_home, name='caixa_home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('abrir-caixa/', views.abrir_caixa, name='abrir_caixa'),
    path('fechar-caixa/', views.fechar_caixa, name='fechar_caixa'),
    path('buscar-produto/', views.ajax_buscar_produto, name='buscar_produto'),
    path('buscar-cliente-nfc/', views.ajax_buscar_cliente_nfc, name='buscar_cliente_nfc'),
    path('finalizar-venda/', views.ajax_finalizar_venda, name='finalizar_venda'),
    path('sync-pull/', views.ajax_sync_snapshot, name='sync_pull'),
    path('sync-push/', views.ajax_sync_push, name='sync_push'),
    path('save-config/', views.ajax_save_config, name='save_config'),
    # Mercado Pago PIX
    path('pix/gerar/', views.ajax_gerar_pix, name='gerar_pix'),
    path('pix/status/', views.ajax_status_pix, name='status_pix'),
    path('sync-mp/', views.ajax_sync_mp, name='sync_mp'),
]
