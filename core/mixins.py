from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse


class TenantViewMixin(LoginRequiredMixin):
    """
    Mixin para views que filtra queryset automaticamente pela empresa do usuário.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request, 'empresa') and self.request.empresa:
            return qs.filter(empresa=self.request.empresa)
        return qs.none()

    def form_valid(self, form):
        form.instance.empresa = self.request.empresa
        return super().form_valid(form)


class TenantAPIViewMixin:
    """
    Mixin para views DRF que filtra queryset automaticamente pela empresa.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        empresa = getattr(self.request, 'empresa', None)
        if empresa:
            return qs.filter(empresa=empresa)
        return qs.none()

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.empresa)
