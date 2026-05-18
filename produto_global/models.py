from django.db import models
from core.models import BaseModel

class ProdutoGlobal(BaseModel):
    """Banco global de produtos por EAN. Compartilhado entre todas as empresas."""
    ean = models.CharField(max_length=13, unique=True, verbose_name='EAN')
    nome = models.CharField(max_length=200, verbose_name='Nome')
    marca = models.CharField(max_length=100, blank=True, verbose_name='Marca')
    categoria = models.CharField(max_length=100, blank=True, verbose_name='Categoria')
    imagem = models.URLField(blank=True, verbose_name='URL Imagem')
    fonte = models.CharField(max_length=50, blank=True, verbose_name='Fonte', help_text='OpenFoodFacts, BarcodeLookup, etc')

    class Meta:
        verbose_name = 'Produto Global'
        verbose_name_plural = 'Produtos Globais'
        ordering = ['nome']

    def __str__(self):
        return f'{self.ean} - {self.nome}'
