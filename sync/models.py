from django.db import models
from core.models import TenantModel

class SyncQueue(TenantModel):
    TIPO_CHOICES = [('create', 'Create'), ('update', 'Update'), ('delete', 'Delete')]
    STATUS_CHOICES = [('pending', 'Pendente'), ('synced', 'Sincronizado'), ('error', 'Erro')]

    pdv_terminal = models.ForeignKey('empresas.PDVTerminal', on_delete=models.SET_NULL, null=True)
    tipo_operacao = models.CharField(max_length=20, choices=TIPO_CHOICES)
    tabela = models.CharField(max_length=100)
    registro_uuid = models.UUIDField()
    payload = models.JSONField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tentativas = models.IntegerField(default=0)
    ultimo_erro = models.TextField(blank=True)

    class Meta:
        ordering = ['created_at']

class SyncLog(TenantModel):
    DIRECAO_CHOICES = [('upload', 'Upload (PDV -> Cloud)'), ('download', 'Download (Cloud -> PDV)')]
    
    pdv_terminal = models.ForeignKey('empresas.PDVTerminal', on_delete=models.SET_NULL, null=True)
    direcao = models.CharField(max_length=20, choices=DIRECAO_CHOICES)
    registros_total = models.IntegerField(default=0)
    registros_sucesso = models.IntegerField(default=0)
    registros_erro = models.IntegerField(default=0)
    duracao_ms = models.IntegerField(default=0)
    detalhes = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
