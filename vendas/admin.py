from django.contrib import admin
from vendas.models import Venda, ItemVenda

class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 0

@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ['numero', 'empresa', 'total', 'forma_pagamento', 'status', 'created_at']
    list_filter = ['status', 'forma_pagamento', 'empresa']
    inlines = [ItemVendaInline]
