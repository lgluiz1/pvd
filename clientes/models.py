from django.db import models
from core.models import TenantModel


class Cliente(TenantModel):
    """Clientes da empresa."""
    nome = models.CharField(max_length=200, verbose_name='Nome')
    cpf = models.CharField(max_length=14, blank=True, verbose_name='CPF')
    telefone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    email = models.EmailField(blank=True, verbose_name='E-mail')
    endereco = models.TextField(blank=True, verbose_name='Endereço')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    nfc_uid = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name='ID do Cartão NFC')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']

    def __str__(self):
        return self.nome
