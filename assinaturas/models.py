import uuid
from django.db import models
from django.utils import timezone
from datetime import date


class ConfigEmail(models.Model):
    """
    Configuracao SMTP para envio de emails de cobranca.
    Apenas 1 registro deve existir. Preencha pelo Django Admin.
    """
    email_host = models.CharField(
        max_length=200, blank=True, default='',
        verbose_name='Servidor SMTP',
        help_text='Ex: smtp.gmail.com, smtp.office365.com'
    )
    email_port = models.PositiveIntegerField(
        default=587,
        verbose_name='Porta SMTP',
        help_text='Geralmente 587 (TLS) ou 465 (SSL)'
    )
    email_user = models.CharField(
        max_length=200, blank=True, default='',
        verbose_name='Email Remetente',
        help_text='Ex: cobranca@suaempresa.com.br'
    )
    email_password = models.CharField(
        max_length=200, blank=True, default='',
        verbose_name='Senha / App Password',
        help_text='Senha do email ou App Password (Gmail requer App Password)'
    )
    email_use_tls = models.BooleanField(
        default=True,
        verbose_name='Usar TLS',
        help_text='Ative para a maioria dos provedores (porta 587)'
    )
    nome_remetente = models.CharField(
        max_length=100, blank=True, default='PDV Cloud - Cobrancas',
        verbose_name='Nome do Remetente',
        help_text='Nome que aparecera no email. Ex: PDV Cloud - Cobrancas'
    )
    ativo = models.BooleanField(
        default=False,
        verbose_name='Envio de Emails Ativo',
        help_text='Marque somente apos configurar e testar os dados acima.'
    )

    class Meta:
        verbose_name = 'Configuracao de Email'
        verbose_name_plural = 'Configuracao de Email'

    def __str__(self):
        status = 'ATIVO' if self.ativo else 'INATIVO'
        return f'Email SMTP ({self.email_host}) - {status}'

    def save(self, *args, **kwargs):
        if not self.pk and ConfigEmail.objects.exists():
            existing = ConfigEmail.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)


class ConfigEfi(models.Model):
    """
    Configuracoes de integracao com a Efi (antiga Gerencianet).
    Apenas 1 registro deve existir.
    """
    client_id = models.CharField(
        max_length=200, blank=True, default='',
        verbose_name='Client ID (Efi)',
        help_text='Obtido no painel da Efi ao criar sua aplicacao.'
    )
    client_secret = models.CharField(
        max_length=200, blank=True, default='',
        verbose_name='Client Secret (Efi)',
        help_text='Obtido no painel da Efi ao criar sua aplicacao.'
    )
    sandbox = models.BooleanField(
        default=True,
        verbose_name='Modo Sandbox (Testes)',
        help_text='Ative para usar o ambiente de testes da Efi. Desative para producao.'
    )
    certificado_pix = models.FileField(
        upload_to='efi/certificados/',
        blank=True, null=True,
        verbose_name='Certificado PIX (.pem)',
        help_text='Arquivo .pem gerado no painel da Efi para cobrar via PIX.'
    )
    chave_pix = models.CharField(
        max_length=100, blank=True, default='',
        verbose_name='Chave PIX cadastrada na Efi',
        help_text='Sua chave PIX registrada na conta Efi.'
    )
    webhook_url = models.URLField(
        blank=True, default='',
        verbose_name='URL do Webhook',
        help_text='URL que a Efi chamara para notificar pagamentos.'
    )
    ativo = models.BooleanField(
        default=False,
        verbose_name='Integracao Ativa',
        help_text='Marque somente quando tiver preenchido todos os campos acima e testado.'
    )

    class Meta:
        verbose_name = 'Configuracao Efi'
        verbose_name_plural = 'Configuracao Efi'

    def __str__(self):
        status = 'ATIVA' if self.ativo else 'INATIVA'
        modo = 'Sandbox' if self.sandbox else 'Producao'
        return f'Efi ({modo}) - {status}'

    def save(self, *args, **kwargs):
        if not self.pk and ConfigEfi.objects.exists():
            existing = ConfigEfi.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)


class PlanoEmpresa(models.Model):
    """
    Define o plano de assinatura de cada empresa cliente.
    Os itens detalhados ficam em ItemPlano.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.OneToOneField(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='plano_assinatura',
        verbose_name='Empresa'
    )
    dia_vencimento = models.PositiveIntegerField(
        default=10,
        verbose_name='Dia do Vencimento',
        help_text='Dia do mes em que a fatura vence (1 a 28).'
    )
    dias_antecedencia = models.PositiveIntegerField(
        default=7,
        verbose_name='Dias de Antecedencia',
        help_text='Quantos dias antes do vencimento a fatura e gerada e o email de lembrete enviado.'
    )
    isento = models.BooleanField(
        default=False,
        verbose_name='Isento de Cobranca',
        help_text='Marque para empresas de teste ou parceiros que nao pagam.'
    )
    observacoes = models.TextField(
        blank=True, default='',
        verbose_name='Observacoes',
        help_text='Anotacoes internas sobre o acordo comercial.'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Plano de Assinatura'
        verbose_name_plural = 'Planos de Assinatura'
        ordering = ['empresa__nome_fantasia']

    @property
    def valor_mensal_total(self):
        """Soma de todos os itens recorrentes."""
        return self.itens.filter(recorrente=True).aggregate(
            total=models.Sum('valor')
        )['total'] or 0

    @property
    def valor_proximo_mes(self):
        """Soma dos itens recorrentes + itens unicos nao cobrados."""
        recorrentes = self.itens.filter(recorrente=True).aggregate(
            total=models.Sum('valor')
        )['total'] or 0
        unicos = self.itens.filter(recorrente=False, cobrado=False).aggregate(
            total=models.Sum('valor')
        )['total'] or 0
        return recorrentes + unicos

    def __str__(self):
        if self.isento:
            return f'{self.empresa.nome_fantasia} - ISENTO'
        return f'{self.empresa.nome_fantasia} - R$ {self.valor_mensal_total}/mes (dia {self.dia_vencimento})'


class ItemPlano(models.Model):
    """
    Item individual de cobranca dentro de um plano.
    Pode ser recorrente (mensal) ou unico (cobra 1x).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plano = models.ForeignKey(
        PlanoEmpresa,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Plano'
    )
    descricao = models.CharField(
        max_length=200,
        verbose_name='Descricao',
        help_text='Ex: Sistema PDV, Bipador, Impressora, Manutencao'
    )
    valor = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='Valor (R$)'
    )
    recorrente = models.BooleanField(
        default=True,
        verbose_name='Cobranca Mensal?',
        help_text='Sim = cobra todo mes. Nao = cobra apenas uma vez no proximo mes.'
    )
    cobrado = models.BooleanField(
        default=False,
        verbose_name='Ja Cobrado?',
        help_text='Para itens de cobranca unica. Marca automaticamente apos gerar a fatura.'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')

    class Meta:
        verbose_name = 'Item do Plano'
        verbose_name_plural = 'Itens do Plano'
        ordering = ['-recorrente', 'descricao']

    def __str__(self):
        tipo = 'Mensal' if self.recorrente else 'Unica'
        return f'{self.descricao} - R$ {self.valor} ({tipo})'


class Fatura(models.Model):
    """
    Fatura individual gerada para uma empresa.
    """
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('atrasado', 'Atrasado'),
        ('cancelada', 'Cancelada'),
    ]

    FORMA_PAGAMENTO_CHOICES = [
        ('', 'Nao informado'),
        ('pix', 'PIX'),
        ('boleto', 'Boleto'),
        ('cartao', 'Cartao de Credito'),
        ('transferencia', 'Transferencia'),
        ('outro', 'Outro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='faturas',
        verbose_name='Empresa'
    )
    descricao = models.CharField(
        max_length=200,
        verbose_name='Descricao',
        help_text='Ex: Mensalidade Maio/2026'
    )
    valor = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='Valor Total (R$)'
    )
    data_emissao = models.DateField(
        default=date.today,
        verbose_name='Data de Emissao'
    )
    data_vencimento = models.DateField(
        verbose_name='Data de Vencimento'
    )
    data_pagamento = models.DateField(
        blank=True, null=True,
        verbose_name='Data do Pagamento'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name='Status'
    )
    forma_pagamento = models.CharField(
        max_length=20,
        choices=FORMA_PAGAMENTO_CHOICES,
        blank=True, default='',
        verbose_name='Forma de Pagamento'
    )

    # Anexos
    arquivo_boleto = models.FileField(
        upload_to='assinaturas/boletos/',
        blank=True, null=True,
        verbose_name='Boleto (PDF)',
        help_text='Anexe o arquivo PDF do boleto para envio ao cliente.'
    )
    comprovante = models.FileField(
        upload_to='assinaturas/comprovantes/',
        blank=True, null=True,
        verbose_name='Comprovante de Pagamento',
        help_text='Anexe o comprovante quando o cliente pagar.'
    )

    # Campos para futura integracao com Efi
    efi_charge_id = models.CharField(max_length=100, blank=True, default='', verbose_name='ID Cobranca (Efi)')
    efi_pix_txid = models.CharField(max_length=100, blank=True, default='', verbose_name='TxID PIX (Efi)')
    efi_boleto_url = models.URLField(blank=True, default='', verbose_name='Link Boleto (Efi)')
    efi_qrcode_pix = models.TextField(blank=True, default='', verbose_name='QR Code PIX (Efi)')

    observacoes = models.TextField(blank=True, default='', verbose_name='Observacoes')
    email_lembrete_enviado = models.BooleanField(default=False, verbose_name='Lembrete Enviado')
    email_recibo_enviado = models.BooleanField(default=False, verbose_name='Recibo Enviado')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Fatura'
        verbose_name_plural = 'Faturas'
        ordering = ['-data_vencimento']
        unique_together = ['empresa', 'descricao']

    def __str__(self):
        return f'{self.empresa.nome_fantasia} - {self.descricao} ({self.get_status_display()})'

    @property
    def esta_vencida(self):
        if self.status in ('pago', 'cancelada'):
            return False
        return self.data_vencimento < date.today()

    def save(self, *args, **kwargs):
        if self.status == 'pendente' and self.data_vencimento < date.today():
            self.status = 'atrasado'
        if self.data_pagamento and self.status not in ('cancelada',):
            self.status = 'pago'
        super().save(*args, **kwargs)


class ItemFatura(models.Model):
    """
    Snapshot dos itens cobrados em uma fatura especifica.
    Permite que o recibo mostre exatamente o que foi pago.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fatura = models.ForeignKey(
        Fatura,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Fatura'
    )
    descricao = models.CharField(max_length=200, verbose_name='Descricao')
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor (R$)')

    class Meta:
        verbose_name = 'Item da Fatura'
        verbose_name_plural = 'Itens da Fatura'

    def __str__(self):
        return f'{self.descricao} - R$ {self.valor}'
