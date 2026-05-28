"""
Servico de integracao com o Mercado Pago para PIX.
Usado pelo PDV Docker para gerar e consultar pagamentos PIX de vendas.
"""
import uuid
import logging

logger = logging.getLogger(__name__)


def gerar_pix(valor, descricao, access_token, email_pagador='cliente@email.com'):
    """
    Gera um pagamento PIX via Mercado Pago.
    Retorna (sucesso, dados) onde dados contem payment_id, qr_code e qr_code_base64.
    """
    try:
        import mercadopago
    except ImportError:
        return False, 'SDK mercadopago nao instalada. Rode: pip install mercadopago'

    if not access_token:
        return False, 'Access Token do Mercado Pago nao configurado.'

    try:
        sdk = mercadopago.SDK(access_token)

        payment_data = {
            'transaction_amount': float(valor),
            'description': descricao[:255],
            'payment_method_id': 'pix',
            'payer': {
                'email': email_pagador,
            },
        }

        # Idempotency key para evitar cobrancas duplicadas
        idempotency_key = str(uuid.uuid4())
        request_options = {
            'headers': {
                'x-idempotency-key': idempotency_key
            }
        }

        result = sdk.payment().create(payment_data, request_options)
        payment = result.get('response', {})
        status_code = result.get('status', 0)

        if status_code in (200, 201):
            transaction_data = payment.get('point_of_interaction', {}).get('transaction_data', {})

            return True, {
                'payment_id': str(payment.get('id', '')),
                'qr_code': transaction_data.get('qr_code', ''),
                'qr_code_base64': transaction_data.get('qr_code_base64', ''),
                'status': payment.get('status', 'pending'),
            }
        else:
            error_msg = payment.get('message', '') or str(payment)
            logger.error(f'[MP] Erro ao criar PIX: {error_msg}')
            return False, f'Erro ao criar PIX: {error_msg}'

    except Exception as e:
        logger.error(f'[MP] Erro inesperado ao gerar PIX: {e}')
        return False, f'Erro inesperado: {str(e)}'


def consultar_pagamento(payment_id, access_token):
    """
    Consulta o status de um pagamento no Mercado Pago.
    Retorna (sucesso, dados) com o status atualizado.
    """
    try:
        import mercadopago
    except ImportError:
        return False, 'SDK mercadopago nao instalada.'

    if not access_token:
        return False, 'Access Token nao configurado.'

    try:
        sdk = mercadopago.SDK(access_token)
        result = sdk.payment().get(int(payment_id))
        payment = result.get('response', {})
        status_code = result.get('status', 0)

        if status_code == 200:
            return True, {
                'payment_id': str(payment.get('id', '')),
                'status': payment.get('status', ''),
                'status_detail': payment.get('status_detail', ''),
                'date_approved': payment.get('date_approved', ''),
            }
        else:
            return False, f'Erro ao consultar: {payment}'

    except Exception as e:
        logger.error(f'[MP] Erro ao consultar pagamento {payment_id}: {e}')
        return False, f'Erro: {str(e)}'
