from rest_framework import viewsets
from core.mixins import TenantAPIViewMixin
from promocoes.models import Promocao
from promocoes.serializers import PromocaoSerializer

class PromocaoViewSet(TenantAPIViewMixin, viewsets.ModelViewSet):
    serializer_class = PromocaoSerializer
    queryset = Promocao.objects.all()
