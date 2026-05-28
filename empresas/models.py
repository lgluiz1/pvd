import uuid
import secrets
from django.db import models
from core.models import BaseModel


class Empresa(BaseModel):
    """
    Modelo principal multi-tenant.
    Cada empresa é um tenant isolado com token único.
    """
    razao_social = models.CharField(max_length=200, verbose_name='Razão Social')
    nome_fantasia = models.CharField(max_length=200, verbose_name='Nome Fantasia')
    cnpj = models.CharField(max_length=18, unique=True, verbose_name='CNPJ')
    token = models.CharField(
        max_length=64, unique=True, editable=False,
        verbose_name='Token API'
    )
    telefone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    email = models.EmailField(blank=True, verbose_name='E-mail Principal')
    email_faturamento = models.EmailField(blank=True, verbose_name='E-mail de Faturamento', help_text='E-mail que receberá os avisos e boletos da assinatura do PDV Cloud')
    endereco = models.TextField(blank=True, verbose_name='Endereço')
    logo = models.ImageField(upload_to='empresas/logos/', blank=True, null=True)
    ativo = models.BooleanField(default=True, verbose_name='Ativa')

    # Endereco estruturado (necessario para emissao de boleto via Efi)
    endereco_rua = models.CharField(max_length=200, blank=True, default='', verbose_name='Rua/Logradouro')
    endereco_numero = models.CharField(max_length=20, blank=True, default='', verbose_name='Numero')
    endereco_bairro = models.CharField(max_length=100, blank=True, default='', verbose_name='Bairro')
    endereco_cep = models.CharField(max_length=10, blank=True, default='', verbose_name='CEP')
    endereco_cidade = models.CharField(max_length=100, blank=True, default='', verbose_name='Cidade')
    endereco_uf = models.CharField(max_length=2, blank=True, default='', verbose_name='UF')
    endereco_complemento = models.CharField(max_length=100, blank=True, default='', verbose_name='Complemento')

    # Configurações de fiado
    config_juros_mensal = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name='Juros Mensal (%)'
    )
    config_juros_atraso = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name='Juros Atraso (%)'
    )
    config_multa_fixa = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Multa Fixa (R$)'
    )
    config_dias_tolerancia = models.IntegerField(
        default=0, verbose_name='Dias de Tolerância'
    )

    # Configurações de impressão
    config_impressao_tamanho = models.CharField(
        max_length=10,
        choices=[
            ('80mm', 'Térmica 80mm (Padrão)'),
            ('58mm', 'Térmica 58mm (Pequena)'),
            ('a4', 'A4 (Folha Inteira)'),
        ],
        default='80mm',
        verbose_name='Tamanho do Papel de Impressão'
    )

    # PIX
    pix_chave = models.CharField(max_length=100, blank=True, verbose_name='Chave PIX')
    pix_tipo = models.CharField(
        max_length=20, blank=True,
        choices=[
            ('cpf', 'CPF'),
            ('cnpj', 'CNPJ'),
            ('email', 'E-mail'),
            ('telefone', 'Telefone'),
            ('aleatoria', 'Chave Aleatória'),
        ],
        verbose_name='Tipo Chave PIX'
    )
    pix_nome = models.CharField(max_length=100, blank=True, verbose_name='Nome Beneficiário PIX')
    pix_cidade = models.CharField(max_length=50, blank=True, verbose_name='Cidade PIX')

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nome_fantasia']

    def __str__(self):
        return self.nome_fantasia

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_hex(32)
        super().save(*args, **kwargs)


class PDVTerminal(BaseModel):
    """
    Representa um caixa/terminal PDV vinculado a uma empresa.
    Cada empresa pode ter múltiplos terminais.
    """
    empresa = models.ForeignKey(
        Empresa, on_delete=models.CASCADE,
        related_name='terminais', verbose_name='Empresa'
    )
    identificador = models.CharField(
        max_length=20, verbose_name='Identificador',
        help_text='Ex: PDV-001'
    )
    nome = models.CharField(
        max_length=100, blank=True, verbose_name='Nome',
        help_text='Ex: Caixa Principal'
    )
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    ultimo_sync = models.DateTimeField(
        blank=True, null=True, verbose_name='Último Sync'
    )

    class Meta:
        verbose_name = 'Terminal PDV'
        verbose_name_plural = 'Terminais PDV'
        unique_together = ['empresa', 'identificador']
        ordering = ['identificador']

    def __str__(self):
        return f'{self.identificador} - {self.empresa.nome_fantasia}'
