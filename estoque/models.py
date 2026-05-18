from django.db import models
from core.models import TenantModel


class MovimentacaoEstoque(TenantModel):
    """Registro de todas movimentações de estoque."""
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
        ('ajuste', 'Ajuste'),
        ('venda', 'Venda'),
        ('devolucao', 'Devolução'),
    ]

    produto = models.ForeignKey(
        'produtos.Produto', on_delete=models.CASCADE,
        related_name='movimentacoes', verbose_name='Produto'
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo')
    quantidade = models.IntegerField(verbose_name='Quantidade')
    quantidade_anterior = models.IntegerField(default=0, verbose_name='Qtd Anterior')
    quantidade_posterior = models.IntegerField(default=0, verbose_name='Qtd Posterior')
    motivo = models.TextField(blank=True, verbose_name='Motivo')
    usuario = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.SET_NULL, null=True,
        verbose_name='Usuário'
    )
    referencia_venda = models.ForeignKey(
        'vendas.Venda', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Venda Ref.'
    )

    class Meta:
        verbose_name = 'Movimentação de Estoque'
        verbose_name_plural = 'Movimentações de Estoque'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.tipo} - {self.produto.nome} ({self.quantidade})'
