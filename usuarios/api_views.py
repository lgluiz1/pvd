from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from usuarios.serializers import UsuarioSerializer, LoginSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """API de login para PDV local."""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = authenticate(
        username=serializer.validated_data['username'],
        password=serializer.validated_data['password']
    )

    if user and user.is_active:
        return Response({
            'user': UsuarioSerializer(user).data,
            'empresa_id': str(user.empresa_id),
        })

    return Response(
        {'error': 'Credenciais inválidas.'},
        status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_me(request):
    """Retorna dados do usuário autenticado."""
    return Response(UsuarioSerializer(request.user).data)
