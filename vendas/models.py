from django.db import models
from core.models import TenantModel


class Venda(TenantModel):
    """Registro de venda com controle de sync."""
    FORMA_PAGAMENTO_CHOICES = [
        ('dinheiro', 'Dinheiro'),
        ('pix', 'PIX'),
        ('cartao_credito', 'Cartão Crédito'),
        ('cartao_debito', 'Cartão Débito'),
        ('fiado', 'Fiado'),
    ]

    STATUS_CHOICES = [
        ('finalizada', 'Finalizada'),
        ('cancelada', 'Cancelada'),
    ]

    SYNC_CHOICES = [
        ('synced', 'Sincronizado'),
        ('pending', 'Pendente'),
        ('error', 'Erro'),
    ]

    numero = models.IntegerField(verbose_name='Número')
    operador = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.SET_NULL, null=True,
        related_name='vendas', verbose_name='Operador'
    )
    cliente = models.ForeignKey(
        'clientes.Cliente', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='vendas', verbose_name='Cliente'
    )
    sessao_caixa = models.ForeignKey(
        'caixa.SessaoCaixa', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='vendas', verbose_name='Sessão Caixa'
    )

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    desconto_tipo = models.CharField(
        max_length=20, blank=True, null=True,
        choices=[('percentual', 'Percentual'), ('fixo', 'Valor Fixo')]
    )
    desconto_valor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    forma_pagamento = models.CharField(
        max_length=20, choices=FORMA_PAGAMENTO_CHOICES, verbose_name='Forma Pagamento'
    )
    valor_recebido = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    troco = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='finalizada')
    cancelada_por = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='vendas_canceladas'
    )
    motivo_cancelamento = models.TextField(blank=True)

    pdv_terminal = models.ForeignKey(
        'empresas.PDVTerminal', on_delete=models.SET_NULL, null=True, blank=True
    )
    sync_status = models.CharField(
        max_length=20, choices=SYNC_CHOICES, default='synced'
    )
    observacoes = models.TextField(blank=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Venda'
        verbose_name_plural = 'Vendas'
        ordering = ['-created_at']

    def __str__(self):
        return f'Venda #{self.numero} - R${self.total}'


class ItemVenda(TenantModel):
    """Item individual de uma venda."""
    venda = models.ForeignKey(
        Venda, on_delete=models.CASCADE,
        related_name='itens', verbose_name='Venda'
    )
    produto = models.ForeignKey(
        'produtos.Produto', on_delete=models.SET_NULL, null=True,
        verbose_name='Produto'
    )
    produto_nome = models.CharField(max_length=200, verbose_name='Nome Produto')
    quantidade = models.IntegerField(default=1, verbose_name='Quantidade')
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Item de Venda'
        verbose_name_plural = 'Itens de Venda'

    def __str__(self):
        return f'{self.produto_nome} x{self.quantidade}'

    def save(self, *args, **kwargs):
        self.subtotal = (self.valor_unitario * self.quantidade) - self.desconto
        super().save(*args, **kwargs)
