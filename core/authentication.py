from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class TokenEmpresaAuthentication(BaseAuthentication):
    """
    Autenticação por token da empresa.
    Usado pelo PDV local para comunicar com o Cloud.
    Header: Authorization: Token <token_empresa>
    """

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Token '):
            return None

        token = auth_header.split(' ')[1]

        from empresas.models import Empresa
        try:
            empresa = Empresa.objects.get(token=token, ativo=True)
        except Empresa.DoesNotExist:
            raise AuthenticationFailed('Token de empresa inválido ou empresa inativa.')

        # Buscar primeiro admin da empresa como user padrão para API
        from usuarios.models import Usuario
        try:
            user = Usuario.objects.filter(empresa=empresa, is_active=True).first()
            if not user:
                raise AuthenticationFailed('Nenhum usuário ativo encontrado para esta empresa.')
        except Usuario.DoesNotExist:
            raise AuthenticationFailed('Usuário não encontrado.')

        request.empresa = empresa
        return (user, token)

    def authenticate_header(self, request):
        return 'Token'
