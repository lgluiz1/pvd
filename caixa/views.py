from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
from caixa.models import SessaoCaixa, Sangria, Suprimento
from vendas.models import Venda


@login_required
def caixa_lista(request):
    """Lista de sessões de caixa."""
    sessoes = SessaoCaixa.objects.filter(empresa=request.empresa)
    return render(request, 'caixa/lista.html', {
        'sessoes': sessoes[:50],
        'page_title': 'Sessões de Caixa',
    })


@login_required
def caixa_abrir(request):
    """Abrir novo caixa."""
    aberta = SessaoCaixa.objects.filter(
        empresa=request.empresa, operador=request.user, status='aberta'
    ).first()
    if aberta:
        messages.warning(request, 'Você já tem um caixa aberto.')
        return redirect('caixa:detalhe', pk=aberta.pk)

    if request.method == 'POST':
        valor = Decimal(request.POST.get('valor_abertura', '0') or '0')
        sessao = SessaoCaixa.objects.create(
            empresa=request.empresa,
            operador=request.user,
            valor_abertura=valor,
        )
        messages.success(request, 'Caixa aberto com sucesso!')
        return redirect('caixa:detalhe', pk=sessao.pk)

    return render(request, 'caixa/abrir.html', {
        'page_title': 'Abrir Caixa',
    })


@login_required
def caixa_fechar(request, pk):
    """Fechar caixa com conferência."""
    sessao = get_object_or_404(SessaoCaixa, pk=pk, empresa=request.empresa)

    if sessao.status == 'fechada':
        messages.warning(request, 'Este caixa já está fechado.')
        return redirect('caixa:detalhe', pk=pk)

    if request.method == 'POST':
        valor_fechamento = Decimal(request.POST.get('valor_fechamento', '0') or '0')

        # Calcular totais
        vendas_sessao = Venda.objects.filter(
            empresa=request.empresa, sessao_caixa=sessao, status='finalizada'
        )

        sessao.total_vendas = vendas_sessao.aggregate(t=Sum('total'))['t'] or 0
        sessao.total_dinheiro = vendas_sessao.filter(forma_pagamento='dinheiro').aggregate(t=Sum('total'))['t'] or 0
        sessao.total_pix = vendas_sessao.filter(forma_pagamento='pix').aggregate(t=Sum('total'))['t'] or 0
        sessao.total_cartao_credito = vendas_sessao.filter(forma_pagamento='cartao_credito').aggregate(t=Sum('total'))['t'] or 0
        sessao.total_cartao_debito = vendas_sessao.filter(forma_pagamento='cartao_debito').aggregate(t=Sum('total'))['t'] or 0
        sessao.total_fiado = vendas_sessao.filter(forma_pagamento='fiado').aggregate(t=Sum('total'))['t'] or 0
        sessao.total_troco = vendas_sessao.aggregate(t=Sum('troco'))['t'] or 0
        sessao.total_sangrias = sessao.sangrias.aggregate(t=Sum('valor'))['t'] or 0
        sessao.total_suprimentos = sessao.suprimentos.aggregate(t=Sum('valor'))['t'] or 0

        valor_esperado = (
            sessao.valor_abertura
            + sessao.total_dinheiro
            - sessao.total_troco
            - sessao.total_sangrias
            + sessao.total_suprimentos
        )

        sessao.valor_fechamento = valor_fechamento
        sessao.divergencia = valor_fechamento - valor_esperado
        sessao.fechamento = timezone.now()
        sessao.status = 'fechada'
        sessao.observacoes = request.POST.get('observacoes', '')
        sessao.save()

        messages.success(request, 'Caixa fechado com sucesso!')
        return redirect('caixa:detalhe', pk=pk)

    return render(request, 'caixa/fechar.html', {
        'sessao': sessao,
        'page_title': 'Fechar Caixa',
    })


@login_required
def caixa_detalhe(request, pk):
    """Detalhe da sessão de caixa."""
    sessao = get_object_or_404(SessaoCaixa, pk=pk, empresa=request.empresa)
    vendas = Venda.objects.filter(sessao_caixa=sessao)
    sangrias = sessao.sangrias.all()
    suprimentos = sessao.suprimentos.all()

    return render(request, 'caixa/detalhe.html', {
        'sessao': sessao,
        'vendas': vendas,
        'sangrias': sangrias,
        'suprimentos': suprimentos,
        'page_title': f'Caixa - {sessao.operador}',
    })


@login_required
def caixa_sangria(request, pk):
    """Registrar sangria."""
    sessao = get_object_or_404(SessaoCaixa, pk=pk, empresa=request.empresa, status='aberta')

    if request.method == 'POST':
        Sangria.objects.create(
            empresa=request.empresa,
            sessao=sessao,
            valor=Decimal(request.POST.get('valor', '0')),
            motivo=request.POST.get('motivo', ''),
            operador=request.user,
        )
        messages.success(request, 'Sangria registrada!')
        return redirect('caixa:detalhe', pk=pk)

    return redirect('caixa:detalhe', pk=pk)


@login_required
def caixa_suprimento(request, pk):
    """Registrar suprimento."""
    sessao = get_object_or_404(SessaoCaixa, pk=pk, empresa=request.empresa, status='aberta')

    if request.method == 'POST':
        Suprimento.objects.create(
            empresa=request.empresa,
            sessao=sessao,
            valor=Decimal(request.POST.get('valor', '0')),
            motivo=request.POST.get('motivo', ''),
            operador=request.user,
        )
        messages.success(request, 'Suprimento registrado!')
        return redirect('caixa:detalhe', pk=pk)

    return redirect('caixa:detalhe', pk=pk)
