import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


class Usuario(AbstractUser):
    """
    Usuário customizado com vínculo à empresa e role.
    Roles: admin, gerente, operador.
    """
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('gerente', 'Gerente'),
        ('operador', 'Operador de Caixa'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='usuarios',
        verbose_name='Empresa',
        null=True, blank=True
    )
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES,
        default='operador', verbose_name='Função'
    )
    telefone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    avatar = models.ImageField(upload_to='usuarios/avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['first_name']

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser

    @property
    def is_gerente(self):
        return self.role in ('admin', 'gerente') or self.is_superuser

    @property
    def is_operador(self):
        return self.role == 'operador'
