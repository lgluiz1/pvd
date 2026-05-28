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

    context = {
        'fatura': fatura,
        'itens': itens,
        'page_title': f'Fatura - {fatura.descricao}',
    }
    return render(request, 'assinaturas/detalhe_fatura.html', context)
