from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from datetime import date
from assinaturas.models import Fatura, PlanoEmpresa
from assinaturas.recibo_pdf import gerar_recibo_pdf


@login_required
def portal_financeiro(request):
    """Portal financeiro visivel apenas para admins da empresa."""
    if not request.user.is_admin:
        return render(request, 'assinaturas/sem_permissao.html')

    empresa = request.empresa
    faturas = Fatura.objects.filter(empresa=empresa).order_by('-data_vencimento')
    plano = PlanoEmpresa.objects.filter(empresa=empresa).first()

    # Atualizar status de pendentes vencidas
    hoje = date.today()
    faturas.filter(status='pendente', data_vencimento__lt=hoje).update(status='atrasado')

    # Calcular resumo
    total_pendente = sum(f.valor for f in faturas if f.status in ('pendente', 'atrasado'))
    total_pago = sum(f.valor for f in faturas if f.status == 'pago')
    tem_inadimplencia = faturas.filter(status='atrasado').exists()

    context = {
        'faturas': faturas,
        'plano': plano,
        'total_pendente': total_pendente,
        'total_pago': total_pago,
        'tem_inadimplencia': tem_inadimplencia,
        'page_title': 'Financeiro',
    }
    return render(request, 'assinaturas/portal_financeiro.html', context)


@login_required
def download_recibo(request, fatura_id):
    """Download do recibo em PDF de uma fatura paga."""
    fatura = get_object_or_404(Fatura, id=fatura_id, empresa=request.empresa)

    if fatura.status != 'pago':
        return HttpResponse('Recibo disponivel apenas para faturas pagas.', status=400)

    pdf_buffer = gerar_recibo_pdf(fatura)
    nome = f'Recibo_{fatura.empresa.nome_fantasia}_{fatura.descricao}.pdf'.replace(' ', '_')

    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nome}"'
    return response


@login_required
def detalhe_fatura(request, fatura_id):
    """Detalhe de uma fatura especifica."""
    fatura = get_object_or_404(Fatura, id=fatura_id, empresa=request.empresa)
    itens = fatura.itens.all()
    
    from assinaturas.models import ConfigEfi
    config_efi = ConfigEfi.objects.first()

    context = {
        'fatura': fatura,
        'itens': itens,
        'config_efi': config_efi,
        'page_title': f'Fatura - {fatura.descricao}',
    }
    return render(request, 'assinaturas/detalhe_fatura.html', context)

@login_required
def status_fatura(request, fatura_id):
    """Retorna o status atual da fatura via JSON (para polling)."""
    from assinaturas.efi_service import consultar_pix_efi
    from assinaturas.emails import enviar_recibo_pagamento

    fatura = get_object_or_404(Fatura, id=fatura_id, empresa=request.empresa)
    
    # Se ainda estiver pendente e tiver txid do PIX, vamos perguntar ativamente para a Efi
    if fatura.status == 'pendente' and fatura.efi_pix_txid:
        ok, dados_pix = consultar_pix_efi(fatura.efi_pix_txid)
        if ok and dados_pix.get('status') == 'CONCLUIDA':
            # Pagamento confirmado!
            fatura.status = 'pago'
            fatura.forma_pagamento = 'pix'
            
            # Extrair data de pagamento se possivel
            pix_detalhes = dados_pix.get('pix', [])
            if pix_detalhes and len(pix_detalhes) > 0:
                horario = pix_detalhes[0].get('horario', '')
                if horario:
                    try:
                        # Pega apenas a data do datetime ISO
                        fatura.data_pagamento = date.fromisoformat(horario[:10])
                    except:
                        fatura.data_pagamento = date.today()
            
            if not fatura.data_pagamento:
                fatura.data_pagamento = date.today()
                
            fatura.save()
            
            # Envia recibo
            if not fatura.email_recibo_enviado:
                try:
                    ok_recibo, _ = enviar_recibo_pagamento(fatura)
                    if ok_recibo:
                        fatura.email_recibo_enviado = True
                        fatura.save(update_fields=['email_recibo_enviado'])
                except:
                    pass

    return JsonResponse({'status': fatura.status})
