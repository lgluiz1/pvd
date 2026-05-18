def global_context(request):
    """Context processor que disponibiliza dados globais em todos os templates."""
    context = {
        'app_name': 'PDV SaaS',
        'app_version': '1.0.0',
    }

    if hasattr(request, 'empresa') and request.empresa:
        context['empresa_atual'] = request.empresa

    if hasattr(request, 'user') and request.user.is_authenticated:
        context['usuario_atual'] = request.user
        context['user_role'] = getattr(request.user, 'role', '')

    return context
