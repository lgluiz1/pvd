from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from financeiro.models import ContaFiado, ParcelaFiado, PagamentoFiado
from clientes.models import Cliente


@login_required
def fiado_lista(request):
    contas = ContaFiado.objects.filter(empresa=request.empresa).select_related('cliente')
    return render(request, 'financeiro/lista.html', {
        'contas': contas, 'page_title': 'Fiados',
    })

@login_required
def fiado_criar(request):
    if request.method == 'POST':
        conta = ContaFiado.objects.create(
            empresa=request.empresa,
            cliente_id=request.POST.get('cliente_id'),
            limite_credito=Decimal(request.POST.get('limite_credito', '0') or '0'),
            juros_mensal=request.empresa.config_juros_mensal,
            juros_atraso=request.empresa.config_juros_atraso,
            multa_atraso=request.empresa.config_multa_fixa,
        )
        messages.success(request, f'Conta fiado criada para {conta.cliente.nome}!')
        return redirect('financeiro:detalhe', pk=conta.pk)

    clientes = Cliente.objects.filter(empresa=request.empresa, ativo=True)
    return render(request, 'financeiro/form.html', {
        'clientes': clientes, 'page_title': 'Nova Conta Fiado',
    })

@login_required
def fiado_detalhe(request, pk):
    conta = get_object_or_404(ContaFiado, pk=pk, empresa=request.empresa)
    parcelas = conta.parcelas.all()

    # Recalcular juros de parcelas atrasadas
    for p in parcelas.filter(status='pendente'):
        p.calcular_juros_multa()

    return render(request, 'financeiro/detalhe.html', {
        'conta': conta, 'parcelas': parcelas,
        'page_title': f'Fiado - {conta.cliente.nome}',
    })

@login_required
def fiado_pagar(request, parcela_id):
    parcela = get_object_or_404(ParcelaFiado, pk=parcela_id, empresa=request.empresa)

    if request.method == 'POST':
        valor = Decimal(request.POST.get('valor', '0'))
        forma = request.POST.get('forma_pagamento', 'dinheiro')

        PagamentoFiado.objects.create(
            empresa=request.empresa,
            parcela=parcela,
            valor=valor,
            forma_pagamento=forma,
            recebido_por=request.user,
            observacao=request.POST.get('observacao', ''),
        )

        parcela.status = 'pago'
        parcela.data_pagamento = timezone.now().date()
        parcela.save()

        # Atualizar saldo devedor
        conta = parcela.conta
        conta.saldo_devedor = max(0, conta.saldo_devedor - valor)
        conta.save()

        messages.success(request, 'Pagamento registrado!')
        return redirect('financeiro:detalhe', pk=conta.pk)

    return redirect('financeiro:lista')
