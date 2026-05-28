"""
Views para gerar cobranca PIX on-demand quando o cliente solicita no portal.
"""
import logging
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from assinaturas.models import Fatura
from assinaturas.efi_service import gerar_pix_efi

logger = logging.getLogger(__name__)


@login_required
def gerar_pix_fatura(request, fatura_id):
    """
    Gera cobranca PIX para uma fatura especifica.
    Chamado quando o cliente clica em 'Pagar com PIX' no portal financeiro.
    Retorna JSON com QR Code para exibicao.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo nao permitido'}, status=405)

    fatura = get_object_or_404(Fatura, id=fatura_id, empresa=request.empresa)

    # Verificar se ja esta paga
    if fatura.status == 'pago':
        return JsonResponse({'error': 'Fatura ja esta paga.'}, status=400)

    # Verificar se ja tem PIX gerado
    if fatura.efi_qrcode_pix:
        return JsonResponse({
            'sucesso': True,
            'qrcode': fatura.efi_qrcode_pix,
            'txid': fatura.efi_pix_txid,
            'mensagem': 'PIX ja gerado anteriormente.',
        })

    # Gerar PIX na Efi
    ok, resultado = gerar_pix_efi(fatura)

    if ok:
        return JsonResponse({
            'sucesso': True,
            'qrcode': resultado.get('qrcode', ''),
            'qrcode_image': resultado.get('qrcode_image', ''),
            'txid': resultado.get('txid', ''),
            'mensagem': 'PIX gerado com sucesso! Escaneie o QR Code para pagar.',
        })
    else:
        return JsonResponse({
            'sucesso': False,
            'mensagem': f'Erro ao gerar PIX: {resultado}',
        }, status=500)
