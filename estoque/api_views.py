from rest_framework import viewsets
from core.mixins import TenantAPIViewMixin
from estoque.models import MovimentacaoEstoque
from estoque.serializers import MovimentacaoEstoqueSerializer


class MovimentacaoViewSet(TenantAPIViewMixin, viewsets.ModelViewSet):
    serializer_class = MovimentacaoEstoqueSerializer
    queryset = MovimentacaoEstoque.objects.all()
