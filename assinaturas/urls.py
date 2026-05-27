from django.urls import path
from assinaturas import views

app_name = 'assinaturas'

urlpatterns = [
    path('financeiro/', views.portal_financeiro, name='portal_financeiro'),
    path('financeiro/fatura/<uuid:fatura_id>/', views.detalhe_fatura, name='detalhe_fatura'),
    path('financeiro/recibo/<uuid:fatura_id>/', views.download_recibo, name='download_recibo'),
]
