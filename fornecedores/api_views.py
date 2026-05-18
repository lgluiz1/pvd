from rest_framework import viewsets
from core.mixins import TenantAPIViewMixin
from fornecedores.models import Fornecedor
from fornecedores.serializers import FornecedorSerializer

class FornecedorViewSet(TenantAPIViewMixin, viewsets.ModelViewSet):
    serializer_class = FornecedorSerializer
    queryset = Fornecedor.objects.all()
    search_fields = ['nome', 'cnpj']
