from django.contrib import admin
from caixa.models import SessaoCaixa, Sangria, Suprimento

@admin.register(SessaoCaixa)
class SessaoCaixaAdmin(admin.ModelAdmin):
    list_display = ['operador', 'empresa', 'status', 'total_vendas', 'abertura', 'fechamento']
    list_filter = ['status', 'empresa']

@admin.register(Sangria)
class SangriaAdmin(admin.ModelAdmin):
    list_display = ['sessao', 'valor', 'motivo', 'operador', 'created_at']

@admin.register(Suprimento)
class SuprimentoAdmin(admin.ModelAdmin):
    list_display = ['sessao', 'valor', 'motivo', 'operador', 'created_at']
