from django.contrib import admin
from empresas.models import Empresa, PDVTerminal


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome_fantasia', 'cnpj', 'telefone', 'ativo', 'created_at']
    list_filter = ['ativo']
    search_fields = ['nome_fantasia', 'razao_social', 'cnpj']
    readonly_fields = ['id', 'token', 'created_at', 'updated_at']


@admin.register(PDVTerminal)
class PDVTerminalAdmin(admin.ModelAdmin):
    list_display = ['identificador', 'empresa', 'ativo', 'ultimo_sync']
    list_filter = ['ativo', 'empresa']
    search_fields = ['identificador', 'empresa__nome_fantasia']
    readonly_fields = ['id', 'created_at', 'updated_at']
