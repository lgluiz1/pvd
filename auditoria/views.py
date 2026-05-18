from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from auditoria.models import LogAuditoria

@login_required
def auditoria_lista(request):
    if not request.user.is_admin:
        messages.error(request, 'Acesso negado.')
        return redirect('relatorios:dashboard')
        
    logs = LogAuditoria.objects.filter(empresa=request.empresa)[:200]
    return render(request, 'auditoria/lista.html', {'logs': logs, 'page_title': 'Auditoria'})
