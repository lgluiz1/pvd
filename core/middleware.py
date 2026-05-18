from django.utils.deprecation import MiddlewareMixin


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware que injeta a empresa do usuário logado no request.
    Permite acesso fácil via request.empresa em qualquer view.
    """

    # URLs que não precisam de empresa
    EXEMPT_URLS = [
        '/login/',
        '/logout/',
        '/admin/',
        '/api/auth/',
        '/static/',
        '/media/',
    ]

    def process_request(self, request):
        request.empresa = None

        # Pular URLs isentas
        for url in self.EXEMPT_URLS:
            if request.path.startswith(url):
                return None

        # Verificar token de API (para PDV local)
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Token '):
            from empresas.models import Empresa
            token = auth_header.split(' ')[1]
            try:
                empresa = Empresa.objects.get(token=token, ativo=True)
                request.empresa = empresa
            except Empresa.DoesNotExist:
                pass
            return None

        # Verificar sessão do usuário logado
        if hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request.user, 'empresa') and request.user.empresa:
                request.empresa = request.user.empresa

        return None
