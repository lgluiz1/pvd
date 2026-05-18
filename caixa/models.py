from django.db import models
from core.models import TenantModel


class SessaoCaixa(TenantModel):
    """Sessão de abertura/fechamento de caixa."""
    STATUS_CHOICES = [
        ('aberta', 'Aberta'),
        ('fechada', 'Fechada'),
    ]

    operador = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.SET_NULL, null=True,
        related_name='sessoes_caixa', verbose_name='Operador'
    )
    pdv_terminal = models.ForeignKey(
        'empresas.PDVTerminal', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Terminal PDV'
    )
    abertura = models.DateTimeField(auto_now_add=True, verbose_name='Abertura')
    fechamento = models.DateTimeField(null=True, blank=True, verbose_name='Fechamento')
    valor_abertura = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name='Valor Abertura (R$)'
    )
    valor_fechamento = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Valor Fechamento (R$)'
    )
    total_vendas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_dinheiro = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_pix = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cartao_credito = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cartao_debito = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_fiado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_troco = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_sangrias = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_suprimentos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    divergencia = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberta')
    observacoes = models.TextField(blank=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Sessão de Caixa'
        verbose_name_plural = 'Sessões de Caixa'
        ordering = ['-abertura']

    def __str__(self):
        return f'Caixa {self.operador} - {self.abertura.strftime("%d/%m/%Y %H:%M")}'


class Sangria(TenantModel):
    """Retirada de dinheiro do caixa."""
    sessao = models.ForeignKey(
        SessaoCaixa, on_delete=models.CASCADE,
        related_name='sangrias', verbose_name='Sessão'
    )
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor (R$)')
    motivo = models.TextField(verbose_name='Motivo')
    operador = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.SET_NULL, null=True
    )

    class Meta:
        verbose_name = 'Sangria'
        verbose_name_plural = 'Sangrias'
        ordering = ['-created_at']

    def __str__(self):
        return f'Sangria R${self.valor} - {self.motivo[:30]}'


class Suprimento(TenantModel):
    """Adição de dinheiro ao caixa."""
    sessao = models.ForeignKey(
        SessaoCaixa, on_delete=models.CASCADE,
        related_name='suprimentos', verbose_name='Sessão'
    )
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor (R$)')
    motivo = models.TextField(verbose_name='Motivo')
    operador = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.SET_NULL, null=True
    )

    class Meta:
        verbose_name = 'Suprimento'
        verbose_name_plural = 'Suprimentos'
        ordering = ['-created_at']

    def __str__(self):
        return f'Suprimento R${self.valor} - {self.motivo[:30]}'
