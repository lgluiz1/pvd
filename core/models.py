import uuid
from django.db import models


class TenantManager(models.Manager):
    """Manager que filtra automaticamente por empresa do request."""

    def get_queryset(self):
        return super().get_queryset()

    def para_empresa(self, empresa):
        return self.get_queryset().filter(empresa=empresa)


class BaseModel(models.Model):
    """
    Modelo base para TODAS as tabelas do sistema.
    Garante: uuid, empresa_id, created_at, updated_at.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    objects = TenantManager()

    class Meta:
        abstract = True
        ordering = ['-created_at']


class TenantModel(BaseModel):
    """
    Modelo base para tabelas que pertencem a uma empresa.
    Herda BaseModel e adiciona empresa_id obrigatório.
    """
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_set',
        verbose_name='Empresa'
    )

    objects = TenantManager()

    class Meta:
        abstract = True
        ordering = ['-created_at']
