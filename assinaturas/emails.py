import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from assinaturas.models import ConfigEmail
from assinaturas.recibo_pdf import gerar_recibo_pdf


def get_admins_emails(empresa):
    """Retorna lista de emails dos usuarios admin vinculados a empresa."""
    from usuarios.models import Usuario
    admins = Usuario.objects.filter(
        empresa=empresa,
        role='admin',
        email__isnull=False,
    ).exclude(email='')
    return list(admins.values_list('email', flat=True))


def _enviar_email(destinatarios, assunto, corpo_html, anexo_pdf=None, anexo_nome=None):
    """Envia email usando as configuracoes SMTP do banco."""
    config = ConfigEmail.objects.first()
    if not config or not config.ativo:
        return False, 'Configuracao de email nao encontrada ou inativa.'

    if not destinatarios:
        return False, 'Nenhum destinatario encontrado.'

    try:
        msg = MIMEMultipart()
        msg['From'] = f'{config.nome_remetente} <{config.email_user}>'
        msg['To'] = ', '.join(destinatarios)
        msg['Subject'] = assunto

        msg.attach(MIMEText(corpo_html, 'html', 'utf-8'))

        if anexo_pdf and anexo_nome:
            pdf_part = MIMEApplication(anexo_pdf.read(), _subtype='pdf')
            pdf_part.add_header('Content-Disposition', 'attachment', filename=anexo_nome)
            msg.attach(pdf_part)

        if config.email_use_tls:
            server = smtplib.SMTP(config.email_host, config.email_port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(config.email_host, config.email_port)

        server.login(config.email_user, config.email_password)
        server.sendmail(config.email_user, destinatarios, msg.as_string())
        server.quit()

        return True, 'Email enviado com sucesso.'
    except Exception as e:
        return False, f'Erro ao enviar email: {str(e)}'


def enviar_lembrete_vencimento(fatura):
    """Envia email de lembrete informando que a fatura esta prestes a vencer."""
    emails = get_admins_emails(fatura.empresa)
    if not emails:
        return False, 'Nenhum admin com email encontrado.'

    itens_html = ''
    for item in fatura.itens.all():
        valor_fmt = f'R$ {item.valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        itens_html += f'<tr><td style="padding:8px;border-bottom:1px solid #eee;">{item.descricao}</td><td style="padding:8px;border-bottom:1px solid #eee;text-align:right;">{valor_fmt}</td></tr>'

    valor_total = f'R$ {fatura.valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    corpo = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f9f9f9;padding:20px;">
        <div style="background:#fff;border-radius:8px;padding:30px;border:1px solid #eee;">
            <h2 style="color:#2c3e50;margin-bottom:5px;">Lembrete de Fatura</h2>
            <p style="color:#7f8c8d;font-size:14px;">PDV Cloud - Sistema de Gestao</p>
            <hr style="border:none;border-top:3px solid #3498db;margin:20px 0;">

            <p style="color:#2c3e50;">Ola,</p>
            <p style="color:#555;">Informamos que a fatura <b>{fatura.descricao}</b> da empresa
            <b>{fatura.empresa.nome_fantasia}</b> esta proxima do vencimento.</p>

            <div style="background:#f0f4f8;border-radius:6px;padding:15px;margin:15px 0;">
                <table style="width:100%;border-collapse:collapse;">
                    <tr><td style="color:#7f8c8d;padding:5px 0;">Vencimento:</td>
                        <td style="text-align:right;font-weight:bold;color:#2c3e50;">{fatura.data_vencimento.strftime('%d/%m/%Y')}</td></tr>
                    <tr><td style="color:#7f8c8d;padding:5px 0;">Valor Total:</td>
                        <td style="text-align:right;font-weight:bold;color:#e74c3c;font-size:18px;">{valor_total}</td></tr>
                </table>
            </div>

            {'<h4 style="color:#2c3e50;">Detalhamento:</h4><table style="width:100%;border-collapse:collapse;">' + itens_html + '</table>' if itens_html else ''}

            <p style="color:#555;margin-top:20px;">Acesse o painel para realizar o pagamento ou entre em contato conosco.</p>

            <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
            <p style="color:#bdc3c7;font-size:11px;text-align:center;">
                Este email foi enviado automaticamente pelo PDV Cloud.<br>
                Luiz Gustavo Tech
            </p>
        </div>
    </div>
    """

    assunto = f'[PDV Cloud] Fatura proxima do vencimento - {fatura.descricao}'
    ok, msg = _enviar_email(emails, assunto, corpo)

    if ok:
        fatura.email_lembrete_enviado = True
        fatura.save(update_fields=['email_lembrete_enviado'])

    return ok, msg


def enviar_alerta_atraso(fatura):
    """Envia email alertando que a fatura esta em atraso."""
    emails = get_admins_emails(fatura.empresa)
    if not emails:
        return False, 'Nenhum admin com email encontrado.'

    valor_total = f'R$ {fatura.valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    corpo = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f9f9f9;padding:20px;">
        <div style="background:#fff;border-radius:8px;padding:30px;border:1px solid #eee;">
            <h2 style="color:#e74c3c;margin-bottom:5px;">Fatura em Atraso</h2>
            <p style="color:#7f8c8d;font-size:14px;">PDV Cloud - Sistema de Gestao</p>
            <hr style="border:none;border-top:3px solid #e74c3c;margin:20px 0;">

            <p style="color:#2c3e50;">Ola,</p>
            <p style="color:#555;">A fatura <b>{fatura.descricao}</b> da empresa
            <b>{fatura.empresa.nome_fantasia}</b> encontra-se <span style="color:#e74c3c;font-weight:bold;">em atraso</span>.</p>

            <div style="background:#fdf0ed;border-radius:6px;padding:15px;margin:15px 0;border-left:4px solid #e74c3c;">
                <table style="width:100%;border-collapse:collapse;">
                    <tr><td style="color:#7f8c8d;padding:5px 0;">Vencimento:</td>
                        <td style="text-align:right;font-weight:bold;color:#e74c3c;">{fatura.data_vencimento.strftime('%d/%m/%Y')}</td></tr>
                    <tr><td style="color:#7f8c8d;padding:5px 0;">Valor:</td>
                        <td style="text-align:right;font-weight:bold;color:#e74c3c;font-size:18px;">{valor_total}</td></tr>
                </table>
            </div>

            <p style="color:#555;">Por favor, regularize o pagamento o mais breve possivel para evitar a suspensao dos servicos.</p>

            <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
            <p style="color:#bdc3c7;font-size:11px;text-align:center;">
                Este email foi enviado automaticamente pelo PDV Cloud.<br>
                Luiz Gustavo Tech
            </p>
        </div>
    </div>
    """

    assunto = f'[PDV Cloud] FATURA EM ATRASO - {fatura.descricao}'
    return _enviar_email(emails, assunto, corpo)


def enviar_recibo_pagamento(fatura):
    """Envia email com o recibo PDF anexado apos confirmacao de pagamento."""
    emails = get_admins_emails(fatura.empresa)
    if not emails:
        return False, 'Nenhum admin com email encontrado.'

    valor_total = f'R$ {fatura.valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    corpo = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f9f9f9;padding:20px;">
        <div style="background:#fff;border-radius:8px;padding:30px;border:1px solid #eee;">
            <h2 style="color:#27ae60;margin-bottom:5px;">Pagamento Confirmado!</h2>
            <p style="color:#7f8c8d;font-size:14px;">PDV Cloud - Sistema de Gestao</p>
            <hr style="border:none;border-top:3px solid #27ae60;margin:20px 0;">

            <p style="color:#2c3e50;">Ola,</p>
            <p style="color:#555;">O pagamento da fatura <b>{fatura.descricao}</b> da empresa
            <b>{fatura.empresa.nome_fantasia}</b> foi <span style="color:#27ae60;font-weight:bold;">confirmado com sucesso</span>!</p>

            <div style="background:#eafaf1;border-radius:6px;padding:15px;margin:15px 0;border-left:4px solid #27ae60;">
                <table style="width:100%;border-collapse:collapse;">
                    <tr><td style="color:#7f8c8d;padding:5px 0;">Valor Pago:</td>
                        <td style="text-align:right;font-weight:bold;color:#27ae60;font-size:18px;">{valor_total}</td></tr>
                    <tr><td style="color:#7f8c8d;padding:5px 0;">Data Pagamento:</td>
                        <td style="text-align:right;font-weight:bold;color:#2c3e50;">
                        {fatura.data_pagamento.strftime('%d/%m/%Y') if fatura.data_pagamento else '-'}</td></tr>
                    <tr><td style="color:#7f8c8d;padding:5px 0;">Forma:</td>
                        <td style="text-align:right;font-weight:bold;color:#2c3e50;">
                        {fatura.get_forma_pagamento_display()}</td></tr>
                </table>
            </div>

            <p style="color:#555;">O recibo de pagamento segue em anexo neste email (PDF).</p>
            <p style="color:#555;">Obrigado pela confianca!</p>

            <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
            <p style="color:#bdc3c7;font-size:11px;text-align:center;">
                Este email foi enviado automaticamente pelo PDV Cloud.<br>
                Luiz Gustavo Tech
            </p>
        </div>
    </div>
    """

    # Gerar PDF do recibo
    pdf_buffer = gerar_recibo_pdf(fatura)
    nome_arquivo = f'Recibo_{fatura.empresa.nome_fantasia}_{fatura.descricao}.pdf'.replace(' ', '_')

    assunto = f'[PDV Cloud] Recibo de Pagamento - {fatura.descricao}'
    ok, msg = _enviar_email(emails, assunto, corpo, anexo_pdf=pdf_buffer, anexo_nome=nome_arquivo)

    if ok:
        fatura.email_recibo_enviado = True
        fatura.save(update_fields=['email_recibo_enviado'])

    return ok, msg
