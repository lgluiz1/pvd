from django.contrib import admin
from fornecedores.models import Fornecedor

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'cnpj', 'telefone', 'ativo']
    list_filter = ['ativo', 'empresa']
    search_fields = ['nome', 'cnpj']
