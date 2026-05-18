from django.db import models
from core.models import TenantModel


class ContaFiado(TenantModel):
    """Conta de fiado de um cliente."""
    cliente = models.ForeignKey(
        'clientes.Cliente', on_delete=models.CASCADE,
        related_name='contas_fiado', verbose_name='Cliente'
    )
    limite_credito = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name='Limite de Crédito (R$)'
    )
    saldo_devedor = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name='Saldo Devedor (R$)'
    )
    juros_mensal = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, verbose_name='Juros Mensal (%)'
    )
    juros_atraso = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, verbose_name='Juros Atraso (%)'
    )
    multa_atraso = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name='Multa Atraso (R$)'
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Conta Fiado'
        verbose_name_plural = 'Contas Fiado'
        ordering = ['cliente__nome']

    def __str__(self):
        return f'Fiado - {self.cliente.nome} (R${self.saldo_devedor})'

    @property
    def disponivel(self):
        return max(0, self.limite_credito - self.saldo_devedor)


class ParcelaFiado(TenantModel):
    """Parcela de fiado vinculada a uma venda."""
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('atrasado', 'Atrasado'),
        ('cancelado', 'Cancelado'),
    ]

    conta = models.ForeignKey(
        ContaFiado, on_delete=models.CASCADE,
        related_name='parcelas', verbose_name='Conta'
    )
    venda = models.ForeignKey(
        'vendas.Venda', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Venda'
    )
    valor_original = models.DecimalField(max_digits=10, decimal_places=2)
    valor_juros = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_multa = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    vencimento = models.DateField(verbose_name='Vencimento')
    data_pagamento = models.DateField(null=True, blank=True, verbose_name='Data Pagamento')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')

    class Meta:
        verbose_name = 'Parcela Fiado'
        verbose_name_plural = 'Parcelas Fiado'
        ordering = ['vencimento']

    def __str__(self):
        return f'Parcela R${self.valor_total} - {self.vencimento}'

    def calcular_juros_multa(self):
        """Calcula juros e multa acumulados se atrasado."""
        from django.utils import timezone
        from decimal import Decimal
        hoje = timezone.now().date()

        if self.status == 'pendente' and hoje > self.vencimento:
            dias_atraso = (hoje - self.vencimento).days
            tolerancia = self.conta.empresa.config_dias_tolerancia

            if dias_atraso > tolerancia:
                meses_atraso = max(1, dias_atraso // 30)
                self.valor_juros = self.valor_original * (self.conta.juros_atraso / Decimal('100')) * meses_atraso
                self.valor_multa = self.conta.multa_atraso
                self.valor_total = self.valor_original + self.valor_juros + self.valor_multa
                self.status = 'atrasado'
                self.save()


class PagamentoFiado(TenantModel):
    """Registro de pagamento de fiado."""
    FORMA_CHOICES = [
        ('dinheiro', 'Dinheiro'),
        ('pix', 'PIX'),
        ('cartao', 'Cartão'),
    ]

    parcela = models.ForeignKey(
        ParcelaFiado, on_delete=models.CASCADE,
        related_name='pagamentos', verbose_name='Parcela'
    )
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Pago (R$)')
    forma_pagamento = models.CharField(max_length=20, choices=FORMA_CHOICES)
    recebido_por = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.SET_NULL, null=True
    )
    observacao = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Pagamento Fiado'
        verbose_name_plural = 'Pagamentos Fiado'
        ordering = ['-created_at']

    def __str__(self):
        return f'Pagamento R${self.valor}'
