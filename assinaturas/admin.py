from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from datetime import date
from assinaturas.models import ConfigEfi, PlanoEmpresa, Fatura


# ─── Config Efi (Singleton) ──────────────────────────────────────────────
@admin.register(ConfigEfi)
class ConfigEfiAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'sandbox', 'ativo', 'chave_pix')
    fieldsets = (
        ('Credenciais da API', {
            'fields': ('client_id', 'client_secret', 'sandbox'),
            'description': 'Preencha com os dados obtidos no painel da Efi (api.efi.com.br).',
        }),
        ('Configuracao PIX', {
            'fields': ('certificado_pix', 'chave_pix'),
            'description': 'Para cobrar via PIX, faca upload do certificado .pem e informe sua chave.',
        }),
        ('Webhook e Status', {
            'fields': ('webhook_url', 'ativo'),
        }),
    )

    def has_add_permission(self, request):
        # Permitir adicionar somente se nao existir nenhum registro
        if ConfigEfi.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


# ─── Plano de Assinatura ─────────────────────────────────────────────────
@admin.register(PlanoEmpresa)
class PlanoEmpresaAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'valor_formatado', 'dia_vencimento', 'badge_isento', 'updated_at')
    list_filter = ('isento', 'dia_vencimento')
    search_fields = ('empresa__nome_fantasia', 'empresa__cnpj')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('empresa',)

    fieldsets = (
        (None, {
            'fields': ('empresa', 'valor_mensal', 'dia_vencimento', 'isento'),
        }),
        ('Anotacoes', {
            'fields': ('observacoes',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Valor Mensal')
    def valor_formatado(self, obj):
        return f'R$ {obj.valor_mensal:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    @admin.display(description='Status', boolean=False)
    def badge_isento(self, obj):
        if obj.isento:
            return format_html(
                '<span style="background:#3498db;color:#fff;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:bold;">ISENTO</span>'
            )
        return format_html(
            '<span style="background:#27ae60;color:#fff;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:bold;">ATIVO</span>'
        )


# ─── Faturas ─────────────────────────────────────────────────────────────
class FaturaAnexosInline(admin.StackedInline):
    """Inline vazio, usado apenas para manter a estrutura."""
    model = Fatura
    extra = 0


@admin.register(Fatura)
class FaturaAdmin(admin.ModelAdmin):
    list_display = (
        'empresa', 'descricao', 'valor_formatado',
        'data_vencimento', 'data_pagamento',
        'badge_status', 'tem_boleto', 'tem_comprovante'
    )
    list_filter = ('status', 'data_vencimento', 'empresa')
    search_fields = ('empresa__nome_fantasia', 'descricao', 'empresa__cnpj')
    date_hierarchy = 'data_vencimento'
    readonly_fields = ('created_at', 'updated_at', 'efi_charge_id', 'efi_pix_txid', 'efi_boleto_url', 'efi_qrcode_pix')
    autocomplete_fields = ('empresa',)
    list_per_page = 30

    fieldsets = (
        ('Dados da Fatura', {
            'fields': ('empresa', 'descricao', 'valor', 'data_emissao', 'data_vencimento'),
        }),
        ('Pagamento', {
            'fields': ('status', 'data_pagamento'),
        }),
        ('Anexos', {
            'fields': ('arquivo_boleto', 'comprovante'),
        }),
        ('Integracao Efi (Automatico)', {
            'fields': ('efi_charge_id', 'efi_pix_txid', 'efi_boleto_url', 'efi_qrcode_pix'),
            'classes': ('collapse',),
            'description': 'Estes campos serao preenchidos automaticamente quando a integracao com a Efi estiver ativa.',
        }),
        ('Observacoes', {
            'fields': ('observacoes',),
            'classes': ('collapse',),
        }),
    )

    actions = ['marcar_como_pago', 'marcar_como_cancelada', 'atualizar_status_vencidas']

    @admin.display(description='Valor')
    def valor_formatado(self, obj):
        return f'R$ {obj.valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    @admin.display(description='Status')
    def badge_status(self, obj):
        colors = {
            'pago': ('#27ae60', '#fff'),
            'pendente': ('#f39c12', '#fff'),
            'atrasado': ('#e74c3c', '#fff'),
            'cancelada': ('#95a5a6', '#fff'),
        }
        bg, fg = colors.get(obj.status, ('#999', '#fff'))
        label = obj.get_status_display().upper()
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;border-radius:4px;font-size:11px;font-weight:bold;">{}</span>',
            bg, fg, label
        )

    @admin.display(description='Boleto', boolean=True)
    def tem_boleto(self, obj):
        return bool(obj.arquivo_boleto)

    @admin.display(description='Comprovante', boolean=True)
    def tem_comprovante(self, obj):
        return bool(obj.comprovante)

    # ─── Acoes em lote ───
    @admin.action(description='Marcar selecionadas como PAGO')
    def marcar_como_pago(self, request, queryset):
        count = queryset.update(status='pago', data_pagamento=date.today())
        self.message_user(request, f'{count} fatura(s) marcada(s) como paga(s).')

    @admin.action(description='Marcar selecionadas como CANCELADA')
    def marcar_como_cancelada(self, request, queryset):
        count = queryset.update(status='cancelada')
        self.message_user(request, f'{count} fatura(s) cancelada(s).')

    @admin.action(description='Atualizar status de faturas vencidas')
    def atualizar_status_vencidas(self, request, queryset):
        hoje = date.today()
        count = Fatura.objects.filter(
            status='pendente',
            data_vencimento__lt=hoje
        ).update(status='atrasado')
        self.message_user(request, f'{count} fatura(s) atualizada(s) para ATRASADO.')
