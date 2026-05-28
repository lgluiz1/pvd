from django.urls import path
from assinaturas import views, pix_views

app_name = 'assinaturas'

urlpatterns = [
    path('assinatura/', views.portal_financeiro, name='portal_financeiro'),
    path('assinatura/fatura/<uuid:fatura_id>/', views.detalhe_fatura, name='detalhe_fatura'),
    path('assinatura/recibo/<uuid:fatura_id>/', views.download_recibo, name='download_recibo'),
    path('assinatura/pix/<uuid:fatura_id>/', pix_views.gerar_pix_fatura, name='gerar_pix'),
]
