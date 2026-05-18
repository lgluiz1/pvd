from django.db import models
from core.models import TenantModel, BaseModel


class Categoria(TenantModel):
    """Categorias de produtos por empresa."""
    nome = models.CharField(max_length=100, verbose_name='Nome')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    ativo = models.BooleanField(default=True, verbose_name='Ativa')

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        unique_together = ['empresa', 'nome']
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Embalagem(TenantModel):
    """Tipos de embalagens/cargas para facilitar a entrada de estoque."""
    nome = models.CharField(max_length=100, verbose_name='Nome da Embalagem', help_text='Ex: Caixa de Ovos, Saco de Batata')
    quantidade_itens = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Quantidade Padrão (Unidades/Kilos)')
    ativo = models.BooleanField(default=True, verbose_name='Ativa')

    class Meta:
        verbose_name = 'Embalagem'
        verbose_name_plural = 'Embalagens'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.quantidade_itens})'


class Produto(TenantModel):
    """Produto cadastrado por empresa com cálculo automático de preço."""
    nome = models.CharField(max_length=200, verbose_name='Nome')
    categoria = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='produtos', verbose_name='Categoria'
    )
    marca = models.CharField(max_length=100, blank=True, verbose_name='Marca')
    codigo_barras = models.CharField(
        max_length=50, blank=True, verbose_name='Código de Barras'
    )
    sem_codigo_barras = models.BooleanField(
        default=False, verbose_name='Sem Código de Barras'
    )
    
    UNIDADE_CHOICES = [
        ('un', 'Unidade (un)'),
        ('kg', 'Quilos (kg)'),
        ('dz', 'Dúzia (dz)'),
        ('fd', 'Fardo (fd)'),
        ('cx', 'Caixa (cx)'),
        ('lt', 'Litro (lt)'),
    ]
    unidade_medida = models.CharField(
        max_length=10, choices=UNIDADE_CHOICES, default='un', verbose_name='Unidade de Medida'
    )

    codigo_interno = models.CharField(
        max_length=20, blank=True, verbose_name='Código Interno',
        help_text='Gerado automaticamente para produtos sem código de barras'
    )

    # Preços
    valor_compra = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Valor de Compra (R$)'
    )
    lucro_percentual = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name='Lucro (%)'
    )
    valor_venda = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Valor de Venda (R$)'
    )

    # Compra em caixa
    comprado_em_caixa = models.BooleanField(
        default=False, verbose_name='Comprado em Caixa'
    )
    valor_caixa = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name='Valor da Caixa (R$)'
    )
    qtd_itens_caixa = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='Quantidade na Caixa (ou Kilos)'
    )

    # Estoque
    quantidade = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name='Quantidade em Estoque')
    estoque_minimo = models.DecimalField(max_digits=10, decimal_places=3, default=5, verbose_name='Estoque Mínimo')

    # Media
    imagem = models.ImageField(
        upload_to='produtos/', blank=True, null=True, verbose_name='Imagem'
    )

    # Status
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    favorito = models.BooleanField(default=False, verbose_name='Favorito')

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        # Calcular valor de venda automaticamente (apenas se lucro for alterado e venda não)
        if self.valor_compra and self.lucro_percentual:
            from decimal import Decimal
            self.valor_venda = self.valor_compra * (1 + self.lucro_percentual / Decimal('100'))

        # Gerar código interno se sem código de barras
        if self.sem_codigo_barras and not self.codigo_interno:
            self._gerar_codigo_interno()

        super().save(*args, **kwargs)

    def _gerar_codigo_interno(self):
        """Gera código interno automático (ex: HORT0001)."""
        prefixo = 'INT'
        if self.categoria:
            prefixo = self.categoria.nome[:4].upper()

        ultimo = Produto.objects.filter(
            empresa=self.empresa,
            codigo_interno__startswith=prefixo
        ).count()

        self.codigo_interno = f'{prefixo}{str(ultimo + 1).zfill(4)}'

    @property
    def estoque_baixo(self):
        return self.quantidade <= self.estoque_minimo

    @property
    def estoque_critico(self):
        return self.quantidade == 0


class HistoricoPreco(TenantModel):
    """Registro histórico de alterações de preço."""
    produto = models.ForeignKey(
        Produto, on_delete=models.CASCADE,
        related_name='historico_precos', verbose_name='Produto'
    )
    valor_compra = models.DecimalField(max_digits=10, decimal_places=2)
    valor_venda = models.DecimalField(max_digits=10, decimal_places=2)
    lucro_percentual = models.DecimalField(max_digits=5, decimal_places=2)
    usuario = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.SET_NULL, null=True,
        verbose_name='Alterado por'
    )
    observacao = models.TextField(blank=True, verbose_name='Observação')

    class Meta:
        verbose_name = 'Histórico de Preço'
        verbose_name_plural = 'Histórico de Preços'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.produto.nome} - R${self.valor_venda} em {self.created_at}'
