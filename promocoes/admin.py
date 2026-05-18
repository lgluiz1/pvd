from django.contrib import admin
from promocoes.models import Promocao
@admin.register(Promocao)
class PromocaoAdmin(admin.ModelAdmin):
    list_display = ['produto', 'tipo', 'valor', 'data_inicio', 'data_fim', 'ativo']
    list_filter = ['ativo', 'tipo', 'empresa']
