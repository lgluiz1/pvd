"""
Webhook para receber notificacoes da Efi (pagamento confirmado, cancelado, etc).
A Efi faz POST com um token, e nosso sistema consulta a API para obter o status.
"""
import logging
from datetime import date
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def efi_notification_webhook(request):
    """
    Recebe POST da Efi com token de notificacao.
    Consulta a Efi para obter status atualizado da cobranca.
    Atualiza a fatura no sistema e envia recibo se pago.
    """
    from assinaturas.models import Fatura
    from assinaturas.efi_service import consultar_notificacao_efi
    from assinaturas.emails import enviar_recibo_pagamento

    # A Efi envia o token no POST body
    token = request.POST.get('notification', '')
    if not token:
        logger.warning('[Webhook Efi] POST recebido sem token de notificacao.')
        return HttpResponse(status=200)  # Retornar 200 para nao reenviar

    logger.info(f'[Webhook Efi] Notificacao recebida - token: {token}')

    # Consultar Efi para obter detalhes
    ok, data = consultar_notificacao_efi(token)
    if not ok:
        logger.error(f'[Webhook Efi] Erro ao consultar notificacao: {data}')
        return HttpResponse(status=200)

    if not data or not isinstance(data, list):
        logger.warning(f'[Webhook Efi] Dados inesperados: {data}')
        return HttpResponse(status=200)

    # Pegar o ultimo evento (mais recente)
    ultimo_evento = data[-1]
    status_atual = ultimo_evento.get('status', {}).get('current', '')
    charge_id = str(ultimo_evento.get('identifiers', {}).get('charge_id', ''))
    custom_id = ultimo_evento.get('custom_id', '')

    logger.info(f'[Webhook Efi] charge_id={charge_id} status={status_atual} custom_id={custom_id}')

    if not charge_id:
        logger.warning('[Webhook Efi] charge_id nao encontrado na notificacao.')
        return HttpResponse(status=200)

    # Buscar fatura pelo charge_id
    try:
        fatura = Fatura.objects.get(efi_charge_id=charge_id)
    except Fatura.DoesNotExist:
        # Tentar buscar pelo custom_id (UUID da fatura)
        if custom_id:
            try:
                fatura = Fatura.objects.get(id=custom_id)
            except Fatura.DoesNotExist:
                logger.warning(f'[Webhook Efi] Fatura nao encontrada: charge_id={charge_id} custom_id={custom_id}')
                return HttpResponse(status=200)
        else:
            logger.warning(f'[Webhook Efi] Fatura nao encontrada: charge_id={charge_id}')
            return HttpResponse(status=200)
    except Fatura.MultipleObjectsReturned:
        fatura = Fatura.objects.filter(efi_charge_id=charge_id).first()

    # Processar baseado no status
    if status_atual == 'paid':
        # Pagamento confirmado!
        received_date = ultimo_evento.get('received_by_bank_at', '')
        if received_date:
            try:
                fatura.data_pagamento = date.fromisoformat(received_date)
            except (ValueError, TypeError):
                fatura.data_pagamento = date.today()
        else:
            fatura.data_pagamento = date.today()

        fatura.status = 'pago'
        if not fatura.forma_pagamento:
            fatura.forma_pagamento = 'boleto'
        fatura.save()

        logger.info(f'[Webhook Efi] Fatura PAGA: {fatura.descricao} - {fatura.empresa.nome_fantasia}')

        # Enviar recibo automaticamente
        if not fatura.email_recibo_enviado:
            try:
                ok_recibo, msg_recibo = enviar_recibo_pagamento(fatura)
                if ok_recibo:
                    logger.info(f'[Webhook Efi] Recibo enviado para {fatura.empresa.nome_fantasia}')
                else:
                    logger.warning(f'[Webhook Efi] Erro ao enviar recibo: {msg_recibo}')
            except Exception as e:
                logger.error(f'[Webhook Efi] Erro ao enviar recibo: {e}')

    elif status_atual in ('canceled', 'expired'):
        fatura.status = 'cancelada'
        fatura.save(update_fields=['status'])
        logger.info(f'[Webhook Efi] Fatura {status_atual}: {fatura.descricao} - {fatura.empresa.nome_fantasia}')

    elif status_atual == 'unpaid':
        fatura.status = 'atrasado'
        fatura.save(update_fields=['status'])
        logger.info(f'[Webhook Efi] Fatura ATRASADA: {fatura.descricao} - {fatura.empresa.nome_fantasia}')

    return HttpResponse(status=200)
