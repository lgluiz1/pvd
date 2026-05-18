from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count
from django.utils import timezone
from decimal import Decimal
from vendas.models import Venda, ItemVenda
from produtos.models import Produto
from estoque.models import MovimentacaoEstoque


@login_required
def venda_lista(request):
    """Lista de vendas."""
    vendas = Venda.objects.filter(empresa=request.empresa)

    # Filtros
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    status = request.GET.get('status', '')
    pagamento = request.GET.get('pagamento', '')

    if data_inicio:
        vendas = vendas.filter(created_at__date__gte=data_inicio)
    if data_fim:
        vendas = vendas.filter(created_at__date__lte=data_fim)
    if status:
        vendas = vendas.filter(status=status)
    if pagamento:
        vendas = vendas.filter(forma_pagamento=pagamento)

    totais = vendas.filter(status='finalizada').aggregate(
        total_vendas=Sum('total'),
        qtd_vendas=Count('id'),
    )

    return render(request, 'vendas/lista.html', {
        'vendas': vendas[:100],
        'totais': totais,
        'page_title': 'Vendas',
    })


@login_required
def venda_detalhe(request, pk):
    """Detalhe de uma venda."""
    venda = get_object_or_404(Venda, pk=pk, empresa=request.empresa)
    itens = venda.itens.all()

    return render(request, 'vendas/detalhe.html', {
        'venda': venda,
        'itens': itens,
        'page_title': f'Venda #{venda.numero}',
    })


@login_required
def venda_cancelar(request, pk):
    """Cancelar uma venda (admin/gerente)."""
    if not request.user.is_gerente:
        messages.error(request, 'Sem permissão.')
        return redirect('vendas:lista')

    venda = get_object_or_404(Venda, pk=pk, empresa=request.empresa)

    if request.method == 'POST':
        motivo = request.POST.get('motivo', '').strip()
        if not motivo:
            messages.error(request, 'Informe o motivo do cancelamento.')
            return redirect('vendas:detalhe', pk=pk)

        venda.status = 'cancelada'
        venda.cancelada_por = request.user
        venda.motivo_cancelamento = motivo
        venda.save()

        # Devolver estoque
        for item in venda.itens.all():
            if item.produto:
                qtd_anterior = item.produto.quantidade
                item.produto.quantidade += item.quantidade
                item.produto.save()

                MovimentacaoEstoque.objects.create(
                    empresa=request.empresa,
                    produto=item.produto,
                    tipo='devolucao',
                    quantidade=item.quantidade,
                    quantidade_anterior=qtd_anterior,
                    quantidade_posterior=item.produto.quantidade,
                    motivo=f'Cancelamento venda #{venda.numero}',
                    usuario=request.user,
                    referencia_venda=venda,
                )

        messages.success(request, f'Venda #{venda.numero} cancelada.')

    return redirect('vendas:lista')


@login_required
def venda_criar_api(request):
    """Criar venda via AJAX (usado pelo PDV web)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    import json
    data = json.loads(request.body)

    # Gerar próximo número
    ultimo_numero = Venda.objects.filter(empresa=request.empresa).count()
    numero = ultimo_numero + 1

    # Criar venda
    venda = Venda.objects.create(
        empresa=request.empresa,
        numero=numero,
        operador=request.user,
        cliente_id=data.get('cliente_id'),
        sessao_caixa_id=data.get('sessao_caixa_id'),
        subtotal=Decimal(str(data.get('subtotal', 0))),
        desconto_tipo=data.get('desconto_tipo', ''),
        desconto_valor=Decimal(str(data.get('desconto_valor', 0))),
        total=Decimal(str(data.get('total', 0))),
        forma_pagamento=data.get('forma_pagamento', 'dinheiro'),
        valor_recebido=Decimal(str(data.get('valor_recebido', 0))) if data.get('valor_recebido') else None,
        troco=Decimal(str(data.get('troco', 0))),
        observacoes=data.get('observacoes', ''),
    )

    # Criar itens e baixar estoque
    for item_data in data.get('itens', []):
        produto = Produto.objects.get(id=item_data['produto_id'], empresa=request.empresa)
        qtd = int(item_data.get('quantidade', 1))

        ItemVenda.objects.create(
            empresa=request.empresa,
            venda=venda,
            produto=produto,
            produto_nome=produto.nome,
            quantidade=qtd,
            valor_unitario=Decimal(str(item_data.get('valor_unitario', produto.valor_venda))),
            desconto=Decimal(str(item_data.get('desconto', 0))),
        )

        # Baixar estoque
        qtd_anterior = produto.quantidade
        produto.quantidade = max(0, produto.quantidade - qtd)
        produto.save()

        MovimentacaoEstoque.objects.create(
            empresa=request.empresa,
            produto=produto,
            tipo='venda',
            quantidade=qtd,
            quantidade_anterior=qtd_anterior,
            quantidade_posterior=produto.quantidade,
            motivo=f'Venda #{numero}',
            usuario=request.user,
            referencia_venda=venda,
        )

    return JsonResponse({
        'success': True,
        'venda_id': str(venda.id),
        'numero': venda.numero,
        'total': str(venda.total),
    })
