from django.contrib import admin
from django.utils.html import format_html
from datetime import date
from empresas.models import Empresa, PDVTerminal
from assinaturas.models import Fatura, PlanoEmpresa


class FaturaInline(admin.TabularInline):
    """Mostra as faturas dentro da pagina de edicao da Empresa."""
    model = Fatura
    extra = 0
    fields = ('descricao', 'valor', 'data_vencimento', 'status', 'data_pagamento', 'arquivo_boleto')
    readonly_fields = ()
    show_change_link = True
    ordering = ('-data_vencimento',)


class PlanoInline(admin.StackedInline):
    """Mostra o plano de assinatura dentro da pagina da Empresa."""
    model = PlanoEmpresa
    extra = 0
    max_num = 1
    fields = ('valor_mensal_total', 'dia_vencimento', 'dias_antecedencia', 'isento', 'observacoes')
    readonly_fields = ('valor_mensal_total',)


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome_fantasia', 'cnpj', 'telefone', 'badge_assinatura', 'ativo', 'created_at']
    list_filter = ['ativo']
    search_fields = ['nome_fantasia', 'razao_social', 'cnpj']
    readonly_fields = ['id', 'token', 'created_at', 'updated_at']
    inlines = [PlanoInline, FaturaInline]

    fieldsets = (
        (None, {
            'fields': ('id', 'razao_social', 'nome_fantasia', 'cnpj', 'token', 'telefone', 'email', 'logo', 'ativo'),
        }),
        ('Endereco para Boleto (Efi)', {
            'fields': ('endereco_rua', 'endereco_numero', 'endereco_complemento', 'endereco_bairro', 'endereco_cep', 'endereco_cidade', 'endereco_uf'),
            'description': 'Preencha para emissao automatica de boletos via Efi. Sem esses dados, o boleto nao sera gerado.',
        }),
        ('Configuracoes de Fiado', {
            'fields': ('config_juros_mensal', 'config_juros_atraso', 'config_multa_fixa', 'config_dias_tolerancia'),
            'classes': ('collapse',),
        }),
        ('Configuracoes de Impressao', {
            'fields': ('config_impressao_tamanho',),
            'classes': ('collapse',),
        }),
        ('PIX (Recebimento de Vendas)', {
            'fields': ('pix_chave', 'pix_tipo', 'pix_nome', 'pix_cidade'),
            'classes': ('collapse',),
        }),
        ('Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Assinatura')
    def badge_assinatura(self, obj):
        """Calcula o status da assinatura baseado nas faturas."""
        # Verifica se tem plano e se e isento
        plano = getattr(obj, 'plano_assinatura', None)
        if plano and plano.isento:
            return format_html(
                '<span style="background:#3498db;color:#fff;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:bold;">ISENTO</span>'
            )

        # Verifica se tem faturas vencidas
        tem_atrasada = Fatura.objects.filter(
            empresa=obj,
            status__in=['atrasado', 'pendente'],
            data_vencimento__lt=date.today()
        ).exists()

        if tem_atrasada:
            return format_html(
                '<span style="background:#e74c3c;color:#fff;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:bold;">INADIMPLENTE</span>'
            )

        # Sem plano cadastrado
        if not plano:
            return format_html(
                '<span style="background:#95a5a6;color:#fff;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:bold;">SEM PLANO</span>'
            )

        return format_html(
            '<span style="background:#27ae60;color:#fff;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:bold;">ADIMPLENTE</span>'
        )


@admin.register(PDVTerminal)
class PDVTerminalAdmin(admin.ModelAdmin):
    list_display = ['identificador', 'empresa', 'ativo', 'ultimo_sync']
    list_filter = ['ativo', 'empresa']
    search_fields = ['identificador', 'empresa__nome_fantasia']
    readonly_fields = ['id', 'created_at', 'updated_at']
