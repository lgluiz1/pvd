from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from produto_global.services import buscar_produto_por_ean

@login_required
def buscar_ean(request):
    """API interna para buscar produto por EAN."""
    ean = request.GET.get('ean', '').strip()
    if not ean:
        return JsonResponse({'found': False, 'error': 'EAN não informado'})
    resultado = buscar_produto_por_ean(ean)
    return JsonResponse(resultado)
