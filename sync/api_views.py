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
            'id': str(u.id),
            'username': u.username,
            'password': u.password,  # Hashed password securely transmitted
            'first_name': u.first_name,
            'last_name': u.last_name,
            'nome_completo': u.get_full_name(),
            'email': u.email,
            'role': getattr(u, 'role', 'operador'),
            'is_active': u.is_active,
        })
        
    clientes_list = []
    from financeiro.models import ContaFiado
    for c in clientes:
        conta, _ = ContaFiado.objects.get_or_create(
            empresa=empresa,
            cliente=c,
            defaults={'limite_credito': 0, 'saldo_devedor': 0}
        )
        clientes_list.append({
            'id': str(c.id),
            'nome': c.nome,
            'cpf': c.cpf,
            'telefone': c.telefone,
            'email': c.email,
            'endereco': c.endereco,
            'observacoes': c.observacoes,
            'nfc_uid': c.nfc_uid,
            'ativo': c.ativo,
            'limite_credito': float(conta.limite_credito),
            'saldo_devedor': float(conta.saldo_devedor),
        })
    
    return Response({
        'produtos': ProdutoSerializer(produtos, many=True).data,
        'categorias': CategoriaSerializer(categorias, many=True).data,
        'usuarios': usuarios_list,
        'clientes': clientes_list,
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_upload(request):
    """Recebe fila de mudanças do PDV (vendas locais para a nuvem)."""
    empresa = request.empresa
    vendas_dados = request.data.get('vendas', [])
    
    from django.db import transaction
    from decimal import Decimal
    from datetime import datetime
    from django.utils import timezone
    
    from vendas.models import Venda, ItemVenda
    from produtos.models import Produto
    from clientes.models import Cliente
    from estoque.models import MovimentacaoEstoque
    from financeiro.models import ContaFiado, ParcelaFiado
    
    vendas_processadas = 0
    
    with transaction.atomic():
        for v in vendas_dados:
            local_id = v.get('local_id')
            if not local_id:
                continue
                
            # Evitar duplicar se a venda já existe no Cloud
            if Venda.objects.filter(id=local_id, empresa=empresa).exists():
                continue
                
            # Buscar maior número de venda + 1
            last_venda = Venda.objects.filter(empresa=empresa).order_by('-numero').first()
            numero = (last_venda.numero + 1) if last_venda else 1
            
            # Mapear forma de pagamento
            forma_pag = v.get('metodo_pagamento', 'dinheiro')
            if forma_pag == 'debito':
                forma_pag = 'cartao_debito'
            elif forma_pag == 'credito':
                forma_pag = 'cartao_credito'
                
            # Buscar cliente se fornecido
            cliente_id = v.get('cliente_id')
            cliente = None
            if cliente_id:
                cliente = Cliente.objects.filter(id=cliente_id, empresa=empresa).first()
                
            # Criar Venda no Cloud
            venda = Venda.objects.create(
                id=local_id,
                empresa=empresa,
                numero=numero,
                cliente=cliente,
                operador=request.user,
                subtotal=Decimal(str(v.get('total', 0))),
                total=Decimal(str(v.get('total', 0))),
                forma_pagamento=forma_pag,
                status='finalizada',
                sync_status='synced',
                created_at=datetime.fromisoformat(v.get('created_at')) if v.get('created_at') else timezone.now()
            )
            
            # Criar itens e baixar estoque
            for item in v.get('itens', []):
                prod_id = item.get('produto_id')
                try:
                    produto = Produto.objects.get(id=prod_id, empresa=empresa)
                except Produto.DoesNotExist:
                    continue
                    
                qtd = int(item.get('quantidade', 1))
                valor_uni = Decimal(str(item.get('valor_unitario', produto.valor_venda)))
                
                ItemVenda.objects.create(
                    empresa=empresa,
                    venda=venda,
                    produto=produto,
                    produto_nome=produto.nome,
                    quantidade=qtd,
                    valor_unitario=valor_uni,
                    desconto=Decimal('0'),
                )
                
                # Baixar estoque na nuvem
                qtd_anterior = produto.quantidade
                produto.quantidade = max(0, produto.quantidade - qtd)
                produto.save()
                
                # Registrar movimentação na nuvem
                MovimentacaoEstoque.objects.create(
                    empresa=empresa,
                    produto=produto,
                    tipo='venda',
                    quantidade=qtd,
                    quantidade_anterior=qtd_anterior,
                    quantidade_posterior=produto.quantidade,
                    motivo=f'Venda #{numero} (Sincronizada via PDV Local)',
                    usuario=request.user,
                    referencia_venda=venda,
                )
                
            # Se for fiado, registrar na conta de fiado
            if forma_pag == 'fiado' and cliente:
                conta, _ = ContaFiado.objects.get_or_create(
                    empresa=empresa,
                    cliente=cliente,
                    defaults={'limite_credito': 0, 'saldo_devedor': 0}
                )
                total_venda = Decimal(str(v.get('total', 0)))
                conta.saldo_devedor += total_venda
                conta.save()
                
                # Criar Parcela de Fiado
                vencimento = (timezone.now() + timezone.timedelta(days=30)).date()
                ParcelaFiado.objects.create(
                    empresa=empresa,
                    conta=conta,
                    venda=venda,
                    valor_original=total_venda,
                    valor_total=total_venda,
                    vencimento=vencimento,
                    status='pendente'
                )
                
            vendas_processadas += 1
            
    return Response({'status': 'ok', 'processed': vendas_processadas})
