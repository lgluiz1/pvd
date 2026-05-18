from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import F
from produtos.models import Produto
from estoque.models import MovimentacaoEstoque


@login_required
def estoque_lista(request):
    """Visão geral do estoque."""
    produtos = Produto.objects.filter(empresa=request.empresa, ativo=True)

    filtro = request.GET.get('filtro', '')
    if filtro == 'baixo':
        produtos = produtos.filter(quantidade__lte=F('estoque_minimo'))
    elif filtro == 'zerado':
        produtos = produtos.filter(quantidade=0)
    elif filtro == 'normal':
        produtos = produtos.filter(quantidade__gt=F('estoque_minimo'))

    return render(request, 'estoque/lista.html', {
        'produtos': produtos,
        'page_title': 'Estoque',
    })


@login_required
def estoque_movimentar(request):
    """Registrar movimentação manual de estoque."""
    if request.method == 'POST':
        produto_id = request.POST.get('produto_id')
        tipo = request.POST.get('tipo')
        quantidade = int(request.POST.get('quantidade', 0))
        motivo = request.POST.get('motivo', '')

        try:
            produto = Produto.objects.get(id=produto_id, empresa=request.empresa)
        except Produto.DoesNotExist:
            messages.error(request, 'Produto não encontrado.')
            return redirect('estoque:lista')

        qtd_anterior = produto.quantidade

        if tipo == 'entrada':
            produto.quantidade += quantidade
        elif tipo == 'saida':
            produto.quantidade = max(0, produto.quantidade - quantidade)
        elif tipo == 'ajuste':
            produto.quantidade = quantidade

        produto.save()

        MovimentacaoEstoque.objects.create(
            empresa=request.empresa,
            produto=produto,
            tipo=tipo,
            quantidade=quantidade,
            quantidade_anterior=qtd_anterior,
            quantidade_posterior=produto.quantidade,
            motivo=motivo,
            usuario=request.user,
        )

        messages.success(request, f'Estoque de "{produto.nome}" atualizado!')
        return redirect('estoque:lista')

    produtos = Produto.objects.filter(empresa=request.empresa, ativo=True)
    return render(request, 'estoque/movimentar.html', {
        'produtos': produtos,
        'page_title': 'Movimentar Estoque',
    })


@login_required
def estoque_historico(request, produto_id):
    """Histórico de movimentações de um produto."""
    movimentacoes = MovimentacaoEstoque.objects.filter(
        empresa=request.empresa, produto_id=produto_id
    )[:50]

    return render(request, 'estoque/historico.html', {
        'movimentacoes': movimentacoes,
        'page_title': 'Histórico de Estoque',
    })


@login_required
def estoque_alertas(request):
    """Produtos com estoque baixo ou zerado."""
    produtos_baixo = Produto.objects.filter(
        empresa=request.empresa, ativo=True,
        quantidade__lte=F('estoque_minimo'),
        quantidade__gt=0
    )
    produtos_zerado = Produto.objects.filter(
        empresa=request.empresa, ativo=True,
        quantidade=0
    )

    return render(request, 'estoque/alertas.html', {
        'produtos_baixo': produtos_baixo,
        'produtos_zerado': produtos_zerado,
        'page_title': 'Alertas de Estoque',
    })
