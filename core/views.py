from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


@login_required
def home_redirect(request):
    """Redireciona para dashboard se logado."""
    return redirect('relatorios:dashboard')
