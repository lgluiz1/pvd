def registrar_log_auditoria(request, acao, detalhes=''):
    from auditoria.models import LogAuditoria
    if not hasattr(request, 'empresa') or not request.empresa:
        return
        
    ip = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT')
    
    LogAuditoria.objects.create(
        empresa=request.empresa,
        usuario=request.user if request.user.is_authenticated else None,
        acao=acao,
        detalhes=detalhes,
        ip=ip,
        user_agent=user_agent
    )
