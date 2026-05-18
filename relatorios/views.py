from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from vendas.models import Venda
from estoque.models import MovimentacaoEstoque

@login_required
def dashboard(request):
    """Dashboard principal."""
    hoje = timezone.now().date()
    inicio_mes = hoje.replace(day=1)
    
    vendas_hoje = Venda.objects.filter(
        empresa=request.empresa, created_at__date=hoje, status='finalizada'
    ).aggregate(total=Sum('total'), qtd=Count('id'))
    
    vendas_mes = Venda.objects.filter(
        empresa=request.empresa, created_at__date__gte=inicio_mes, status='finalizada'
    ).aggregate(total=Sum('total'), qtd=Count('id'))
    
    ultimas_vendas = Venda.objects.filter(empresa=request.empresa).order_by('-created_at')[:5]
    
    context = {
        'vendas_hoje': vendas_hoje,
        'vendas_mes': vendas_mes,
        'ultimas_vendas': ultimas_vendas,
        'page_title': 'Dashboard',
    }
    return render(request, 'relatorios/dashboard.html', context)
