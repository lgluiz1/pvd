"""
Servico de integracao com a Efi (antiga Gerencianet).
Gera boletos, cobracas PIX e consulta notificacoes de pagamento.
"""
import logging
from decimal import Decimal
from assinaturas.models import ConfigEfi

logger = logging.getLogger(__name__)


def _get_efi_client():
    """Retorna instancia do EfiPay configurada, ou None se nao disponivel."""
    config = ConfigEfi.objects.first()
    if not config or not config.ativo:
        logger.warning('[Efi] Integracao inativa ou nao configurada.')
        return None, None

    try:
        from efipay import EfiPay
    except ImportError:
        logger.error('[Efi] SDK efipay nao instalada. Rode: pip install efipay')
        return None, None

    credentials = {
        'client_id': config.client_id,
        'client_secret': config.client_secret,
        'sandbox': config.sandbox,
    }

    # Certificado PIX (opcional, necessario apenas para PIX)
    if config.certificado_pix:
        credentials['certificate'] = config.certificado_pix.path

    try:
        efi = EfiPay(credentials)
        return efi, config
    except Exception as e:
        logger.error(f'[Efi] Erro ao inicializar SDK: {e}')
        return None, None


def _empresa_tem_dados_boleto(empresa):
    """Verifica se a empresa tem dados minimos para gerar boleto."""
    campos = [empresa.cnpj, empresa.razao_social, empresa.endereco_rua,
              empresa.endereco_numero, empresa.endereco_bairro,
              empresa.endereco_cep, empresa.endereco_cidade, empresa.endereco_uf]
    return all(c and str(c).strip() for c in campos)


def gerar_boleto_efi(fatura, notification_url=None):
    """
    Gera boleto (Bolix) na Efi via One Step.
    Salva charge_id, link do boleto e link do PDF na fatura.

    Retorna (sucesso: bool, mensagem: str)
    """
    efi, config = _get_efi_client()
    if not efi:
        return False, 'Integracao Efi inativa ou nao configurada.'

    empresa = fatura.empresa

    if not _empresa_tem_dados_boleto(empresa):
        logger.warning(f'[Efi] Empresa {empresa.nome_fantasia} sem dados de endereco para boleto.')
        return False, 'Empresa sem dados de endereco completos para emissao de boleto.'

    # Valor em centavos (Efi exige inteiro)
    valor_centavos = int(fatura.valor * 100)

    # Montar itens da fatura
    itens_efi = []
    itens_fatura = fatura.itens.all()
    if itens_fatura.exists():
        for item in itens_fatura:
            itens_efi.append({
                'name': item.descricao[:255],
                'value': int(item.valor * 100),
                'amount': 1,
            })
    else:
        # Fallback: item unico com valor total
        itens_efi.append({
            'name': fatura.descricao[:255],
            'value': valor_centavos,
            'amount': 1,
        })

    # Limpar CNPJ (remover pontos, barras, tracos)
    cnpj_limpo = ''.join(c for c in empresa.cnpj if c.isdigit())
    cep_limpo = ''.join(c for c in empresa.endereco_cep if c.isdigit())

    body = {
        'items': itens_efi,
        'payment': {
            'banking_billet': {
                'customer': {
                    'juridical_person': {
                        'corporate_name': empresa.razao_social[:255],
                        'cnpj': cnpj_limpo,
                    },
                    'email': empresa.email or '',
                    'phone_number': ''.join(c for c in (empresa.telefone or '') if c.isdigit())[:11] or None,
                    'address': {
                        'street': empresa.endereco_rua[:200],
                        'number': empresa.endereco_numero[:20],
                        'neighborhood': empresa.endereco_bairro[:100],
                        'zipcode': cep_limpo[:8],
                        'city': empresa.endereco_cidade[:100],
                        'complement': empresa.endereco_complemento[:100] or '',
                        'state': empresa.endereco_uf[:2].upper(),
                    },
                },
                'expire_at': fatura.data_vencimento.strftime('%Y-%m-%d'),
                'configurations': {
                    'days_to_write_off': 30,  # Baixa automatica 30 dias apos vencimento
                    'fine': 200,              # Multa 2%
                    'interest': 33,           # Juros 0,033% ao dia (~1% ao mes)
                },
                'message': f'PDV Cloud - {fatura.descricao}',
            },
        },
    }

    # Remover phone_number se vazio
    if not body['payment']['banking_billet']['customer'].get('phone_number'):
        body['payment']['banking_billet']['customer'].pop('phone_number', None)
    # Remover email se vazio
    if not body['payment']['banking_billet']['customer'].get('email'):
        body['payment']['banking_billet']['customer'].pop('email', None)

    # Adicionar notification_url se fornecida
    if notification_url:
        body['metadata'] = {
            'notification_url': notification_url,
            'custom_id': str(fatura.id),
        }

    try:
        response = efi.create_charge_one_step(body=body)

        if response.get('code') == 200:
            data = response.get('data', {})
            fatura.efi_charge_id = str(data.get('charge_id', ''))
            fatura.efi_boleto_url = data.get('link', '') or data.get('billet_link', '')

            # QR Code PIX do Bolix (se disponivel)
            pix_data = data.get('pix', {})
            if pix_data:
                fatura.efi_qrcode_pix = pix_data.get('qrcode', '')

            # Salvar link do PDF
            pdf_data = data.get('pdf', {})
            if pdf_data:
                # Salvar URL do PDF no campo de observacoes ou no campo boleto
                fatura.observacoes = (fatura.observacoes or '') + f'\nPDF Boleto: {pdf_data.get("charge", "")}'

            fatura.forma_pagamento = 'boleto'
            fatura.save()

            logger.info(f'[Efi] Boleto gerado: charge_id={fatura.efi_charge_id} empresa={empresa.nome_fantasia}')
            return True, f'Boleto gerado com sucesso. Charge ID: {fatura.efi_charge_id}'
        else:
            msg = f'Resposta inesperada da Efi: {response}'
            logger.error(f'[Efi] {msg}')
            return False, msg

    except Exception as e:
        msg = f'Erro ao gerar boleto na Efi: {str(e)}'
        logger.error(f'[Efi] {msg}')
        return False, msg


def gerar_pix_efi(fatura):
    """
    Gera cobranca PIX imediata na Efi.
    Retorna (sucesso, dados) onde dados contem qrcode e qrcode_image.
    """
    efi, config = _get_efi_client()
    if not efi:
        return False, 'Integracao Efi inativa ou nao configurada.'

    if not config.chave_pix:
        return False, 'Chave PIX nao configurada na Efi.'

    if not config.certificado_pix:
        return False, 'Certificado PIX (.pem) nao configurado na Efi.'

    # Valor com 2 casas decimais como string
    valor_str = f'{fatura.valor:.2f}'

    body = {
        'calendario': {'expiracao': 3600},  # Expira em 1 hora
        'valor': {'original': valor_str},
        'chave': config.chave_pix,
        'solicitacaoPagador': f'PDV Cloud - {fatura.descricao}',
        'infoAdicionais': [
            {'nome': 'Empresa', 'valor': fatura.empresa.nome_fantasia},
            {'nome': 'Fatura', 'valor': fatura.descricao},
        ],
    }

    try:
        # Criar cobranca PIX
        response = efi.pix_create_immediate_charge(body=body)

        if 'txid' in response:
            txid = response['txid']
            fatura.efi_pix_txid = txid

            # Gerar QR Code
            qr_response = efi.pix_generate_QRCode(params={'id': response['loc']['id']})
            qrcode = qr_response.get('qrcode', '')
            qrcode_image = qr_response.get('imagemQrcode', '')

            fatura.efi_qrcode_pix = qrcode
            fatura.save()

            logger.info(f'[Efi] PIX gerado: txid={txid} empresa={fatura.empresa.nome_fantasia}')
            return True, {
                'txid': txid,
                'qrcode': qrcode,
                'qrcode_image': qrcode_image,
            }
        else:
            msg = f'Resposta inesperada da Efi PIX: {response}'
            logger.error(f'[Efi] {msg}')
            return False, msg

    except Exception as e:
        msg = f'Erro ao gerar PIX na Efi: {str(e)}'
        logger.error(f'[Efi] {msg}')
        return False, msg


def consultar_notificacao_efi(token):
    """
    Consulta detalhes de uma notificacao da Efi.
    Retorna (sucesso, dados) com historico completo da cobranca.
    """
    efi, config = _get_efi_client()
    if not efi:
        return False, 'Integracao Efi inativa.'

    try:
        params = {'token': token}
        response = efi.get_notification(params=params)

        if response.get('code') == 200:
            return True, response.get('data', [])
        else:
            return False, f'Resposta inesperada: {response}'

    except Exception as e:
        msg = f'Erro ao consultar notificacao Efi: {str(e)}'
        logger.error(f'[Efi] {msg}')
        return False, msg
