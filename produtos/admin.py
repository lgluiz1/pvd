from django.contrib import admin
from produtos.models import Produto, Categoria, HistoricoPreco


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'ativo']
    list_filter = ['ativo', 'empresa']
    search_fields = ['nome']


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'codigo_barras', 'valor_venda', 'quantidade', 'ativo']
    list_filter = ['ativo', 'empresa', 'categoria']
    search_fields = ['nome', 'codigo_barras', 'codigo_interno']


@admin.register(HistoricoPreco)
class HistoricoPrecoAdmin(admin.ModelAdmin):
    list_display = ['produto', 'valor_compra', 'valor_venda', 'lucro_percentual', 'created_at']
    list_filter = ['empresa']
