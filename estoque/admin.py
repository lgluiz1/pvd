from django.contrib import admin
from estoque.models import MovimentacaoEstoque

@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['produto', 'tipo', 'quantidade', 'usuario', 'created_at']
    list_filter = ['tipo', 'empresa']
