from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from core.mixins import TenantAPIViewMixin
from produtos.models import Produto
from produtos.serializers import ProdutoSerializer


class ProdutoViewSet(TenantAPIViewMixin, viewsets.ModelViewSet):
    serializer_class = ProdutoSerializer
    queryset = Produto.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categoria', 'ativo', 'favorito', 'sem_codigo_barras']
    search_fields = ['nome', 'codigo_barras', 'codigo_interno', 'marca']
    ordering_fields = ['nome', 'valor_venda', 'quantidade', 'created_at']
