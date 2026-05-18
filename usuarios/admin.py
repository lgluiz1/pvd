from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from usuarios.models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'first_name', 'last_name', 'empresa', 'role', 'is_active']
    list_filter = ['role', 'is_active', 'empresa']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    fieldsets = UserAdmin.fieldsets + (
        ('PDV', {'fields': ('empresa', 'role', 'telefone', 'avatar')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('PDV', {'fields': ('empresa', 'role', 'telefone')}),
    )
