from django.contrib import admin
from financeiro.models import ContaFiado, ParcelaFiado, PagamentoFiado

@admin.register(ContaFiado)
class ContaFiadoAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'empresa', 'limite_credito', 'saldo_devedor', 'ativo']

@admin.register(ParcelaFiado)
class ParcelaFiadoAdmin(admin.ModelAdmin):
    list_display = ['conta', 'valor_total', 'vencimento', 'status']

@admin.register(PagamentoFiado)
class PagamentoFiadoAdmin(admin.ModelAdmin):
    list_display = ['parcela', 'valor', 'forma_pagamento', 'created_at']
