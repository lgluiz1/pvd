from django.contrib import admin
from produto_global.models import ProdutoGlobal
@admin.register(ProdutoGlobal)
class ProdutoGlobalAdmin(admin.ModelAdmin):
    list_display = ['ean', 'nome', 'marca', 'categoria', 'fonte']
    search_fields = ['ean', 'nome', 'marca']
