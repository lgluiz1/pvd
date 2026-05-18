from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from clientes.models import Cliente
from financeiro.models import ContaFiado


@login_required
def cliente_lista(request):
    clientes = Cliente.objects.filter(empresa=request.empresa)
    busca = request.GET.get('busca', '').strip()
    if busca:
        clientes = clientes.filter(
            Q(nome__icontains=busca) | Q(cpf__icontains=busca) | Q(telefone__icontains=busca)
        )
    return render(request, 'clientes/lista.html', {
        'clientes': clientes, 'busca': busca, 'page_title': 'Clientes',
    })


@login_required
def cliente_criar(request):
    if request.method == 'POST':
        Cliente.objects.create(
            empresa=request.empresa,
            nome=request.POST.get('nome', '').strip(),
            cpf=request.POST.get('cpf', '').strip(),
            telefone=request.POST.get('telefone', '').strip(),
            email=request.POST.get('email', '').strip(),
            endereco=request.POST.get('endereco', '').strip(),
            observacoes=request.POST.get('observacoes', '').strip(),
            nfc_uid=request.POST.get('nfc_uid', '').strip() or None,
        )
        messages.success(request, 'Cliente criado com sucesso!')
        return redirect('clientes:lista')
    return render(request, 'clientes/form.html', {'page_title': 'Novo Cliente'})


@login_required
def cliente_editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk, empresa=request.empresa)
    if request.method == 'POST':
        cliente.nome = request.POST.get('nome', cliente.nome).strip()
        cliente.cpf = request.POST.get('cpf', cliente.cpf).strip()
        cliente.telefone = request.POST.get('telefone', cliente.telefone).strip()
        cliente.email = request.POST.get('email', cliente.email).strip()
        cliente.endereco = request.POST.get('endereco', cliente.endereco).strip()
        cliente.observacoes = request.POST.get('observacoes', cliente.observacoes).strip()
        cliente.nfc_uid = request.POST.get('nfc_uid', '').strip() or None
        cliente.ativo = request.POST.get('ativo') == 'on'
        cliente.save()
        messages.success(request, 'Cliente atualizado!')
        return redirect('clientes:lista')
    return render(request, 'clientes/form.html', {
        'cliente': cliente, 'page_title': f'Editar {cliente.nome}', 'editando': True,
    })


@login_required
def buscar_cliente_nfc(request):
    """API para o PDV offline/local consultar cliente e limites via NFC."""
    uid = request.GET.get('uid', '').strip()
    if not uid:
        return JsonResponse({'found': False, 'error': 'Parâmetro uid é obrigatório.'})

    try:
        cliente = Cliente.objects.get(empresa=request.empresa, nfc_uid=uid, ativo=True)
        
        # Pega a conta de fiado vinculada
        conta, created = ContaFiado.objects.get_or_create(
            empresa=request.empresa,
            cliente=cliente,
            defaults={'limite_credito': 0, 'saldo_devedor': 0}
        )

        return JsonResponse({
            'found': True,
            'cliente': {
                'id': str(cliente.id),
                'nome': cliente.nome,
                'cpf': cliente.cpf,
                'ativo': cliente.ativo,
                'fiado': {
                    'limite_credito': float(conta.limite_credito),
                    'saldo_devedor': float(conta.saldo_devedor),
                    'limite_disponivel': float(conta.disponivel),
                }
            }
        })
    except Cliente.DoesNotExist:
        return JsonResponse({'found': False, 'message': 'Cartão NFC não cadastrado ou inativo.'})
