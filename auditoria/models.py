from django.db import models
from core.models import TenantModel

class LogAuditoria(TenantModel):
    ACAO_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('cancelamento_venda', 'Cancelamento de Venda'),
        ('desconto_manual', 'Desconto Manual'),
        ('alteracao_preco', 'Alteração de Preço'),
        ('abertura_caixa', 'Abertura de Caixa'),
        ('fechamento_caixa', 'Fechamento de Caixa'),
        ('sangria', 'Sangria'),
        ('suprimento', 'Suprimento'),
        ('config_empresa', 'Alteração Configurações'),
    ]

    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, verbose_name='Usuário')
    acao = models.CharField(max_length=50, choices=ACAO_CHOICES, verbose_name='Ação')
    detalhes = models.TextField(blank=True, verbose_name='Detalhes')
    ip = models.CharField(max_length=50, blank=True, null=True, verbose_name='IP')
    user_agent = models.TextField(blank=True, null=True, verbose_name='User Agent')

    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_acao_display()} - {self.usuario} ({self.created_at.strftime("%d/%m/%Y %H:%M")})'
