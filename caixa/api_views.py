from rest_framework import viewsets
from core.mixins import TenantAPIViewMixin
from caixa.models import SessaoCaixa
from caixa.serializers import SessaoCaixaSerializer

class SessaoCaixaViewSet(TenantAPIViewMixin, viewsets.ModelViewSet):
    serializer_class = SessaoCaixaSerializer
    queryset = SessaoCaixa.objects.all()
