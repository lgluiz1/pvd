from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from fornecedores.models import Fornecedor

@login_required
def fornecedor_lista(request):
    fornecedores = Fornecedor.objects.filter(empresa=request.empresa)
    busca = request.GET.get('busca', '').strip()
    if busca:
        fornecedores = fornecedores.filter(Q(nome__icontains=busca) | Q(cnpj__icontains=busca))
    return render(request, 'fornecedores/lista.html', {
        'fornecedores': fornecedores, 'busca': busca, 'page_title': 'Fornecedores',
    })

@login_required
def fornecedor_criar(request):
    if request.method == 'POST':
        Fornecedor.objects.create(
            empresa=request.empresa,
            nome=request.POST.get('nome', '').strip(),
            cnpj=request.POST.get('cnpj', '').strip(),
            telefone=request.POST.get('telefone', '').strip(),
            email=request.POST.get('email', '').strip(),
            endereco=request.POST.get('endereco', '').strip(),
            contato=request.POST.get('contato', '').strip(),
            observacoes=request.POST.get('observacoes', '').strip(),
        )
        messages.success(request, 'Fornecedor criado!')
        return redirect('fornecedores:lista')
    return render(request, 'fornecedores/form.html', {'page_title': 'Novo Fornecedor'})

@login_required
def fornecedor_editar(request, pk):
    f = get_object_or_404(Fornecedor, pk=pk, empresa=request.empresa)
    if request.method == 'POST':
        f.nome = request.POST.get('nome', f.nome).strip()
        f.cnpj = request.POST.get('cnpj', f.cnpj).strip()
        f.telefone = request.POST.get('telefone', f.telefone).strip()
        f.email = request.POST.get('email', f.email).strip()
        f.endereco = request.POST.get('endereco', f.endereco).strip()
        f.contato = request.POST.get('contato', f.contato).strip()
        f.observacoes = request.POST.get('observacoes', f.observacoes).strip()
        f.ativo = request.POST.get('ativo') == 'on'
        f.save()
        messages.success(request, 'Fornecedor atualizado!')
        return redirect('fornecedores:lista')
    return render(request, 'fornecedores/form.html', {
        'fornecedor': f, 'page_title': f'Editar {f.nome}', 'editando': True,
    })
