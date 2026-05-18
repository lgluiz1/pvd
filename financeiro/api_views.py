from rest_framework import viewsets
from core.mixins import TenantAPIViewMixin
from financeiro.models import ContaFiado
from financeiro.serializers import ContaFiadoSerializer

class ContaFiadoViewSet(TenantAPIViewMixin, viewsets.ModelViewSet):
    serializer_class = ContaFiadoSerializer
    queryset = ContaFiado.objects.all()
