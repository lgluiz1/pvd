from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from promocoes.models import Promocao
from produtos.models import Produto

@login_required
def promocao_lista(request):
    promocoes = Promocao.objects.filter(empresa=request.empresa)
    return render(request, 'promocoes/lista.html', {'promocoes': promocoes, 'page_title': 'Promoções'})

@login_required
def promocao_criar(request):
    if request.method == 'POST':
        Promocao.objects.create(
            empresa=request.empresa,
            produto_id=request.POST.get('produto_id'),
            tipo=request.POST.get('tipo', 'percentual'),
            valor=Decimal(request.POST.get('valor', '0')),
            data_inicio=request.POST.get('data_inicio'),
            data_fim=request.POST.get('data_fim'),
            descricao=request.POST.get('descricao', ''),
        )
        messages.success(request, 'Promoção criada!')
        return redirect('promocoes:lista')
    produtos = Produto.objects.filter(empresa=request.empresa, ativo=True)
    return render(request, 'promocoes/form.html', {'produtos': produtos, 'page_title': 'Nova Promoção'})

@login_required
def promocao_toggle(request, pk):
    promo = get_object_or_404(Promocao, pk=pk, empresa=request.empresa)
    promo.ativo = not promo.ativo
    promo.save()
    messages.success(request, f'Promoção {"ativada" if promo.ativo else "desativada"}!')
    return redirect('promocoes:lista')
