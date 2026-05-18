from rest_framework import viewsets
from core.mixins import TenantAPIViewMixin
from clientes.models import Cliente
from clientes.serializers import ClienteSerializer

class ClienteViewSet(TenantAPIViewMixin, viewsets.ModelViewSet):
    serializer_class = ClienteSerializer
    queryset = Cliente.objects.all()
    search_fields = ['nome', 'cpf', 'telefone']
