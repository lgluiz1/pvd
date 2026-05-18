from django.contrib import admin
from clientes.models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'cpf', 'telefone', 'ativo']
    list_filter = ['ativo', 'empresa']
    search_fields = ['nome', 'cpf', 'telefone']
