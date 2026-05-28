from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from empresas.models import Empresa, PDVTerminal
from core.mixins import TenantViewMixin


@login_required
def empresa_config(request):
    """Página de configuração da empresa."""
    empresa = request.empresa
    if not empresa:
        messages.error(request, 'Empresa não encontrada.')
        return redirect('relatorios:dashboard')

    if request.method == 'POST':
        empresa.nome_fantasia = request.POST.get('nome_fantasia', empresa.nome_fantasia)
        empresa.razao_social = request.POST.get('razao_social', empresa.razao_social)
        empresa.telefone = request.POST.get('telefone', empresa.telefone)
        empresa.email = request.POST.get('email', empresa.email)
        empresa.endereco = request.POST.get('endereco', empresa.endereco)
        empresa.config_juros_mensal = request.POST.get('config_juros_mensal', empresa.config_juros_mensal)
        empresa.config_juros_atraso = request.POST.get('config_juros_atraso', empresa.config_juros_atraso)
        empresa.config_multa_fixa = request.POST.get('config_multa_fixa', empresa.config_multa_fixa)
        empresa.config_dias_tolerancia = request.POST.get('config_dias_tolerancia', empresa.config_dias_tolerancia)
        empresa.config_impressao_tamanho = request.POST.get('config_impressao_tamanho', empresa.config_impressao_tamanho)
        empresa.pix_chave = request.POST.get('pix_chave', empresa.pix_chave)
        empresa.pix_tipo = request.POST.get('pix_tipo', empresa.pix_tipo)
        empresa.pix_nome = request.POST.get('pix_nome', empresa.pix_nome)
        empresa.pix_cidade = request.POST.get('pix_cidade', empresa.pix_cidade)
        
        if 'mp_access_token' in request.POST:
            empresa.mp_access_token = request.POST.get('mp_access_token', '').strip()

        if request.FILES.get('logo'):
            empresa.logo = request.FILES['logo']

        empresa.save()
        messages.success(request, 'Configurações atualizadas com sucesso!')
        return redirect('empresas:config')

    terminais = PDVTerminal.objects.filter(empresa=empresa)
    return render(request, 'empresas/config.html', {
        'empresa': empresa,
        'terminais': terminais,
        'page_title': 'Configurações da Empresa',
    })


@login_required
def terminal_criar(request):
    """Criar novo terminal PDV."""
    if request.method == 'POST':
        empresa = request.empresa
        # Gerar próximo identificador
        ultimo = PDVTerminal.objects.filter(empresa=empresa).count()
        identificador = f'PDV-{str(ultimo + 1).zfill(3)}'

        terminal = PDVTerminal.objects.create(
            empresa=empresa,
            identificador=identificador,
            nome=request.POST.get('nome', ''),
        )
        messages.success(request, f'Terminal {identificador} criado com sucesso!')
        return redirect('empresas:config')

    return redirect('empresas:config')


@login_required
def terminal_toggle(request, pk):
    """Ativar/desativar terminal."""
    terminal = get_object_or_404(PDVTerminal, pk=pk, empresa=request.empresa)
    terminal.ativo = not terminal.ativo
    terminal.save()
    status = 'ativado' if terminal.ativo else 'desativado'
    messages.success(request, f'Terminal {terminal.identificador} {status}.')
    return redirect('empresas:config')
