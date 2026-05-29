import uuid
from django.db import models

class ProdutoLocal(models.Model):
    """Cópia local offline dos produtos da Nuvem."""
    id = models.UUIDField(primary_key=True) # ID original do Cloud (UUID)
    nome = models.CharField(max_length=200)
    codigo_barras = models.CharField(max_length=50, blank=True, null=True)
    codigo_interno = models.CharField(max_length=50, blank=True, null=True)
    valor_venda = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unidade_medida = models.CharField(max_length=10, default='un')
    quantidade = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    estoque_minimo = models.DecimalField(max_digits=10, decimal_places=3, default=5)

    def __str__(self):
        return self.nome

    @property
    def estoque_baixo(self):
        return self.quantidade <= self.estoque_minimo


class ClienteLocal(models.Model):
    """Cópia local offline dos clientes da Nuvem para Fiado e NFC."""
    id = models.UUIDField(primary_key=True) # ID original do Cloud (UUID)
    nome = models.CharField(max_length=200)
    nfc_uid = models.CharField(max_length=50, blank=True, null=True)
    limite_credito = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    saldo_devedor = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def limite_disponivel(self):
        return max(self.limite_credito - self.saldo_devedor, 0)

    def __str__(self):
        return self.nome


class SessaoCaixaLocal(models.Model):
    """Sessão de caixa aberta localmente, sincronizada com a nuvem."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operador_username = models.CharField(max_length=150)
    abertura = models.DateTimeField(auto_now_add=True)
    fechamento = models.DateTimeField(null=True, blank=True)
    valor_abertura = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_fechamento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, default='aberta') # aberta, fechada
    observacoes = models.TextField(blank=True, null=True)
    synced = models.BooleanField(default=False)

    class Meta:
        ordering = ['-abertura']

    def __str__(self):
        return f'Caixa Local {self.operador_username} - {self.status}'


class VendaLocal(models.Model):
    """Venda realizada localmente (funciona off/on) enfileirada para sincronização."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sessao = models.ForeignKey(SessaoCaixaLocal, on_delete=models.SET_NULL, null=True, blank=True, related_name='vendas')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pagamento = models.CharField(max_length=20) # dinheiro, debito, credito, pix, fiado
    cliente = models.ForeignKey(ClienteLocal, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, default='finalizada')
    synced = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Venda {self.id} - R$ {self.total}'


class ItemVendaLocal(models.Model):
    """Itens da venda local."""
    venda = models.ForeignKey(VendaLocal, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(ProdutoLocal, on_delete=models.CASCADE)
    quantidade = models.DecimalField(max_digits=10, decimal_places=3)
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.quantidade}x {self.produto.nome}'


class ConfigLocal(models.Model):
    """Configurações de integração com a Nuvem."""
    api_token = models.CharField(max_length=128, blank=True)
    api_cloud_url = models.CharField(max_length=255, default='http://localhost:8000')
    ultimo_sync = models.DateTimeField(blank=True, null=True)
    mp_access_token = models.CharField(max_length=300, blank=True, default='')
    # Dados da Empresa (puxado do Cloud)
    empresa_nome = models.CharField(max_length=200, blank=True, default='Empresa PDV')
    empresa_cnpj = models.CharField(max_length=20, blank=True, default='')
    empresa_telefone = models.CharField(max_length=20, blank=True, default='')
    empresa_endereco = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return "Configuração do POS Local"

    @property
    def mp_configurado(self):
        return bool(self.mp_access_token)


class PagamentoPix(models.Model):
    """Rastreia pagamentos PIX pendentes gerados via Mercado Pago."""
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('approved', 'Aprovado'),
        ('expired', 'Expirado'),
        ('cancelled', 'Cancelado'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venda = models.ForeignKey(VendaLocal, on_delete=models.CASCADE, related_name='pagamentos_pix', null=True, blank=True)
    mp_payment_id = models.CharField(max_length=100, verbose_name='Payment ID (MP)')
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    qr_code = models.TextField(blank=True, default='', verbose_name='PIX Copia e Cola')
    qr_code_base64 = models.TextField(blank=True, default='', verbose_name='QR Code Base64')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'PIX {self.mp_payment_id} - R$ {self.valor} ({self.status})'
