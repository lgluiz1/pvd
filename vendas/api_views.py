from rest_framework import viewsets
from core.mixins import TenantAPIViewMixin
from vendas.models import Venda
from vendas.serializers import VendaSerializer


class VendaViewSet(TenantAPIViewMixin, viewsets.ModelViewSet):
    serializer_class = VendaSerializer
    queryset = Venda.objects.all()
    filterset_fields = ['status', 'forma_pagamento', 'sync_status']
    search_fields = ['numero']
    ordering_fields = ['numero', 'total', 'created_at']
