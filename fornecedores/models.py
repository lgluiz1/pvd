from django.db import models
from core.models import TenantModel

class Fornecedor(TenantModel):
    nome = models.CharField(max_length=200, verbose_name='Nome')
    cnpj = models.CharField(max_length=18, blank=True, verbose_name='CNPJ')
    telefone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    email = models.EmailField(blank=True, verbose_name='E-mail')
    endereco = models.TextField(blank=True, verbose_name='Endereço')
    contato = models.CharField(max_length=100, blank=True, verbose_name='Contato')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'
        ordering = ['nome']

    def __str__(self):
        return self.nome
