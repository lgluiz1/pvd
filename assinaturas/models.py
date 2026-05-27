import uuid
from django.db import models
from django.utils import timezone
from datetime import date


class ConfigEfi(models.Model):
    """
    Configuracoes de integracao com a Efi (antiga Gerencianet).
    Apenas 1 registro deve existir. Quando voce criar sua aplicacao na Efi,
    basta preencher os campos abaixo pelo Django Admin.
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
        help_text='Sua chave PIX registrada na conta Efi (CPF, CNPJ, email ou aleatoria).'
    )
    webhook_url = models.URLField(
        blank=True, default='',
        verbose_name='URL do Webhook',
        help_text='URL que a Efi chamara para notificar pagamentos. Ex: https://pvd.luizgustavo.tech/api/efi/webhook/'
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
        # Garantir que so exista 1 registro
        if not self.pk and ConfigEfi.objects.exists():
            existing = ConfigEfi.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)


class PlanoEmpresa(models.Model):
    """
    Define o valor mensal e dia de vencimento para cada empresa cliente.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.OneToOneField(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='plano_assinatura',
        verbose_name='Empresa'
    )
    valor_mensal = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Valor Mensal (R$)',
        help_text='Valor acordado com o cliente para cobranca mensal.'
    )
    dia_vencimento = models.PositiveIntegerField(
        default=10,
        verbose_name='Dia do Vencimento',
        help_text='Dia do mes em que a fatura vence (1 a 28).'
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

    def __str__(self):
        if self.isento:
            return f'{self.empresa.nome_fantasia} - ISENTO'
        return f'{self.empresa.nome_fantasia} - R$ {self.valor_mensal}/mes (dia {self.dia_vencimento})'


class Fatura(models.Model):
    """
    Fatura individual gerada para uma empresa.
    Pode ser gerada manualmente ou futuramente de forma automatica pela API Efi.
    """
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('atrasado', 'Atrasado'),
        ('cancelada', 'Cancelada'),
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
        verbose_name='Valor (R$)'
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
    efi_charge_id = models.CharField(
        max_length=100, blank=True, default='',
        verbose_name='ID da Cobranca (Efi)',
        help_text='Preenchido automaticamente quando integrado com a Efi.'
    )
    efi_pix_txid = models.CharField(
        max_length=100, blank=True, default='',
        verbose_name='TxID PIX (Efi)',
        help_text='Preenchido automaticamente quando cobrado via PIX Efi.'
    )
    efi_boleto_url = models.URLField(
        blank=True, default='',
        verbose_name='Link do Boleto (Efi)',
        help_text='URL do boleto gerado pela Efi.'
    )
    efi_qrcode_pix = models.TextField(
        blank=True, default='',
        verbose_name='QR Code PIX (Efi)',
        help_text='Payload do QR Code PIX gerado pela Efi.'
    )

    observacoes = models.TextField(
        blank=True, default='',
        verbose_name='Observacoes'
    )

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
        """Retorna True se a fatura esta vencida e nao paga."""
        if self.status in ('pago', 'cancelada'):
            return False
        return self.data_vencimento < date.today()

    def save(self, *args, **kwargs):
        # Atualizar status automaticamente para 'atrasado' se venceu
        if self.status == 'pendente' and self.data_vencimento < date.today():
            self.status = 'atrasado'
        # Se marcou data de pagamento, muda para pago
        if self.data_pagamento and self.status != 'cancelada':
            self.status = 'pago'
        super().save(*args, **kwargs)
