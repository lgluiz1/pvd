from rest_framework import viewsets, permissions
from empresas.models import Empresa
from empresas.serializers import EmpresaSerializer


class EmpresaViewSet(viewsets.ModelViewSet):
    serializer_class = EmpresaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        empresa = getattr(self.request, 'empresa', None)
        if empresa:
            return Empresa.objects.filter(id=empresa.id)
        return Empresa.objects.none()
