"""
Tasks Celery para processamento automatico de faturas.
Roda diariamente as 06h via Celery Beat.
"""
import logging
import calendar
from datetime import date, timedelta
from celery import shared_task
from django.db import models
from django.conf import settings

logger = logging.getLogger(__name__)


def _calcular_data_vencimento(dia_vencimento, referencia=None):
    """
    Calcula a data de vencimento do proximo mes a partir da data de referencia.
    Se o dia nao existe no mes (ex: dia 31 em fevereiro), usa o ultimo dia do mes.
    """
    if referencia is None:
        referencia = date.today()

    # Proximo mes
    if referencia.month == 12:
        ano = referencia.year + 1
        mes = 1
    else:
        ano = referencia.year
        mes = referencia.month + 1

    # Ajustar dia se nao existe no mes
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    dia = min(dia_vencimento, ultimo_dia)

    return date(ano, mes, dia)


def _gerar_descricao_fatura(data_vencimento):
    """Gera descricao padrao para a fatura. Ex: Mensalidade Junho/2026"""
    meses = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Marco', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    nome_mes = meses.get(data_vencimento.month, str(data_vencimento.month))
    return f'Mensalidade {nome_mes}/{data_vencimento.year}'


@shared_task(name='assinaturas.tasks.processar_faturas_diarias')
def processar_faturas_diarias():
    """
    Task principal que roda diariamente as 06h.

    1. Gera faturas para planos cujo vencimento esta proximo
    2. Gera boleto na Efi (se integrada)
    3. Envia email de lembrete para todos os admins
    4. Atualiza faturas vencidas para 'atrasado'
    5. Envia alertas de atraso
    """
    from assinaturas.models import PlanoEmpresa, Fatura, ItemFatura
    from assinaturas.emails import enviar_lembrete_vencimento, enviar_alerta_atraso
    from assinaturas.efi_service import gerar_boleto_efi

    hoje = date.today()
    logger.info(f'[Faturas] Iniciando processamento diario - {hoje}')

    faturas_criadas = 0
    boletos_gerados = 0
    emails_enviados = 0
    faturas_atualizadas = 0

    # ─── ETAPA 1: Gerar novas faturas ────────────────────────────────────
    planos = PlanoEmpresa.objects.filter(isento=False).select_related('empresa')

    for plano in planos:
        try:
            # Calcular data de vencimento do proximo ciclo
            data_venc = _calcular_data_vencimento(plano.dia_vencimento, hoje)

            # Se estamos dentro do periodo de antecedencia
            data_inicio_geracao = data_venc - timedelta(days=plano.dias_antecedencia)

            if hoje < data_inicio_geracao:
                continue  # Ainda nao e hora de gerar

            # Verificar se ja existe fatura para este mes
            descricao = _gerar_descricao_fatura(data_venc)
            ja_existe = Fatura.objects.filter(
                empresa=plano.empresa,
                descricao=descricao,
            ).exists()

            if ja_existe:
                continue  # Fatura ja criada, pular

            # Calcular valor total
            valor_total = plano.valor_proximo_mes
            if valor_total <= 0:
                logger.warning(f'[Faturas] Plano de {plano.empresa.nome_fantasia} tem valor 0, pulando.')
                continue

            # Criar fatura
            fatura = Fatura.objects.create(
                empresa=plano.empresa,
                descricao=descricao,
                valor=valor_total,
                data_emissao=hoje,
                data_vencimento=data_venc,
                status='pendente',
            )

            # Criar itens da fatura (snapshot)
            for item in plano.itens.all():
                # Incluir recorrentes sempre, e unicos nao cobrados
                if item.recorrente or not item.cobrado:
                    ItemFatura.objects.create(
                        fatura=fatura,
                        descricao=item.descricao,
                        valor=item.valor,
                    )
                    # Marcar itens unicos como cobrados
                    if not item.recorrente:
                        item.cobrado = True
                        item.save(update_fields=['cobrado'])

            faturas_criadas += 1
            logger.info(f'[Faturas] Fatura criada: {descricao} - {plano.empresa.nome_fantasia} - R$ {valor_total}')

            # ─── ETAPA 2: Gerar boleto na Efi ────────────────────────────
            # Montar notification_url
            notification_url = None
            allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
            domain = next((h for h in allowed_hosts if h not in ('*', 'localhost', '127.0.0.1', '')), None)
            if domain:
                notification_url = f'https://{domain}/api/efi/webhook/'

            ok_boleto, msg_boleto = gerar_boleto_efi(fatura, notification_url)
            if ok_boleto:
                boletos_gerados += 1
                logger.info(f'[Faturas] Boleto gerado para {plano.empresa.nome_fantasia}')
            else:
                logger.warning(f'[Faturas] Boleto nao gerado para {plano.empresa.nome_fantasia}: {msg_boleto}')

            # ─── ETAPA 3: Enviar email de lembrete ────────────────────────
            ok_email, msg_email = enviar_lembrete_vencimento(fatura)
            if ok_email:
                emails_enviados += 1
                logger.info(f'[Faturas] Email de lembrete enviado para {plano.empresa.nome_fantasia}')
            else:
                logger.warning(f'[Faturas] Email nao enviado para {plano.empresa.nome_fantasia}: {msg_email}')

        except Exception as e:
            logger.error(f'[Faturas] Erro ao processar plano de {plano.empresa.nome_fantasia}: {e}', exc_info=True)
            continue

    # ─── ETAPA 4: Atualizar faturas vencidas ──────────────────────────────
    vencidas = Fatura.objects.filter(
        status='pendente',
        data_vencimento__lt=hoje,
    )
    faturas_atualizadas = vencidas.update(status='atrasado')

    # ─── ETAPA 5: Enviar alertas de atraso (para as que acabaram de vencer) ─
    alertas_enviados = 0
    faturas_atrasadas = Fatura.objects.filter(
        status='atrasado',
        email_lembrete_enviado=True,  # Ja recebeu lembrete
    ).select_related('empresa')

    for fatura in faturas_atrasadas:
        # Enviar alerta apenas se venceu ha 1 dia (evitar spam)
        dias_atraso = (hoje - fatura.data_vencimento).days
        if dias_atraso == 1:
            try:
                ok, msg = enviar_alerta_atraso(fatura)
                if ok:
                    alertas_enviados += 1
            except Exception as e:
                logger.error(f'[Faturas] Erro ao enviar alerta de atraso: {e}')

    resumo = (
        f'[Faturas] Processamento concluido - '
        f'Faturas criadas: {faturas_criadas}, '
        f'Boletos gerados: {boletos_gerados}, '
        f'Emails enviados: {emails_enviados}, '
        f'Vencidas atualizadas: {faturas_atualizadas}, '
        f'Alertas de atraso: {alertas_enviados}'
    )
    logger.info(resumo)
    return resumo
