from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from produtos.serializers import ProdutoSerializer, CategoriaSerializer
from produtos.models import Produto, Categoria
from usuarios.serializers import UsuarioSerializer
from usuarios.models import Usuario
from clientes.serializers import ClienteSerializer
from clientes.models import Cliente

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_snapshot(request):
    """Envia snapshot completo para o PDV (primeiro boot)."""
    empresa = request.empresa
    
    produtos = Produto.objects.filter(empresa=empresa, ativo=True)
    categorias = Categoria.objects.filter(empresa=empresa, ativo=True)
    usuarios = Usuario.objects.filter(empresa=empresa, is_active=True)
    clientes = Cliente.objects.filter(empresa=empresa, ativo=True)
    
    usuarios_list = []
    for u in usuarios:
        usuarios_list.append({
            'id': u.id,
            'username': u.username,
            'password': u.password,  # Hashed password securely transmitted
            'first_name': u.first_name,
            'last_name': u.last_name,
            'nome_completo': u.get_full_name(),
            'email': u.email,
            'role': getattr(u, 'role', 'operador'),
            'is_active': u.is_active,
        })
    
    return Response({
        'produtos': ProdutoSerializer(produtos, many=True).data,
        'categorias': CategoriaSerializer(categorias, many=True).data,
        'usuarios': usuarios_list,
        'clientes': ClienteSerializer(clientes, many=True).data,
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_upload(request):
    """Recebe fila de mudanças do PDV."""
    # TODO: Implementar processamento da fila
    return Response({'status': 'ok'})
