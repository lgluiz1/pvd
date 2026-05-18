from django.db import models
from core.models import TenantModel

class Promocao(TenantModel):
    TIPO_CHOICES = [('percentual', 'Percentual'), ('valor_fixo', 'Valor Fixo')]
    produto = models.ForeignKey('produtos.Produto', on_delete=models.CASCADE, related_name='promocoes')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor do Desconto')
    data_inicio = models.DateTimeField(verbose_name='Início')
    data_fim = models.DateTimeField(verbose_name='Fim')
    ativo = models.BooleanField(default=True)
    descricao = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Promoção'
        verbose_name_plural = 'Promoções'
        ordering = ['-data_inicio']

    def __str__(self):
        return f'{self.produto.nome} - {self.get_tipo_display()} {self.valor}'

    @property
    def vigente(self):
        from django.utils import timezone
        now = timezone.now()
        return self.ativo and self.data_inicio <= now <= self.data_fim
