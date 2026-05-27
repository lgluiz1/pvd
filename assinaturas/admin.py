from django.contrib import admin
from django.utils.html import format_html
from datetime import date
from assinaturas.models import ConfigEmail, ConfigEfi, PlanoEmpresa, ItemPlano, Fatura, ItemFatura


# ─── Config Email (Singleton) ────────────────────────────────────────────
@admin.register(ConfigEmail)
class ConfigEmailAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'email_user', 'ativo')
    fieldsets = (
        ('Servidor SMTP', {
            'fields': ('email_host', 'email_port', 'email_use_tls'),
            'description': 'Dados do servidor de email para envio de cobrancas.',
        }),
        ('Credenciais', {
            'fields': ('email_user', 'email_password', 'nome_remetente'),
        }),
        ('Status', {
            'fields': ('ativo',),
        }),
    )

    def has_add_permission(self, request):
        if ConfigEmail.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


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
        }),
        ('Webhook e Status', {
            'fields': ('webhook_url', 'ativo'),
        }),
    )

    def has_add_permission(self, request):
        if ConfigEfi.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


# ─── Itens do Plano (Inline) ─────────────────────────────────────────────
class ItemPlanoInline(admin.TabularInline):
    model = ItemPlano
    extra = 1
    fields = ('descricao', 'valor', 'recorrente', 'cobrado')
    readonly_fields = ('cobrado',)


# ─── Plano de Assinatura ─────────────────────────────────────────────────
@admin.register(PlanoEmpresa)
class PlanoEmpresaAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'valor_mensal_display', 'valor_proximo_display', 'dia_vencimento', 'dias_antecedencia', 'badge_isento', 'updated_at')
    list_filter = ('isento', 'dia_vencimento')
    search_fields = ('empresa__nome_fantasia', 'empresa__cnpj')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('empresa',)
    inlines = [ItemPlanoInline]

    fieldsets = (
        (None, {
            'fields': ('empresa', 'dia_vencimento', 'dias_antecedencia', 'isento'),
        }),
        ('Anotacoes', {
            'fields': ('observacoes',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Valor Mensal')
    def valor_mensal_display(self, obj):
        v = obj.valor_mensal_total
        return f'R$ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    @admin.display(description='Proximo Mes')
    def valor_proximo_display(self, obj):
        v = obj.valor_proximo_mes
        return f'R$ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    @admin.display(description='Status')
    def badge_isento(self, obj):
        if obj.isento:
            return format_html(
                '<span style="background:#3498db;color:#fff;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:bold;">ISENTO</span>'
            )
        return format_html(
            '<span style="background:#27ae60;color:#fff;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:bold;">ATIVO</span>'
        )


# ─── Itens da Fatura (Inline) ────────────────────────────────────────────
class ItemFaturaInline(admin.TabularInline):
    model = ItemFatura
    extra = 0
    fields = ('descricao', 'valor')


# ─── Faturas ─────────────────────────────────────────────────────────────
@admin.register(Fatura)
class FaturaAdmin(admin.ModelAdmin):
    list_display = (
        'empresa', 'descricao', 'valor_formatado',
        'data_vencimento', 'data_pagamento', 'forma_pagamento',
        'badge_status', 'tem_boleto', 'tem_comprovante'
    )
    list_filter = ('status', 'forma_pagamento', 'data_vencimento', 'empresa')
    search_fields = ('empresa__nome_fantasia', 'descricao', 'empresa__cnpj')
    date_hierarchy = 'data_vencimento'
    readonly_fields = ('created_at', 'updated_at', 'efi_charge_id', 'efi_pix_txid', 'efi_boleto_url', 'efi_qrcode_pix', 'email_lembrete_enviado', 'email_recibo_enviado')
    autocomplete_fields = ('empresa',)
    list_per_page = 30
    inlines = [ItemFaturaInline]

    fieldsets = (
        ('Dados da Fatura', {
            'fields': ('empresa', 'descricao', 'valor', 'data_emissao', 'data_vencimento'),
        }),
        ('Pagamento', {
            'fields': ('status', 'forma_pagamento', 'data_pagamento'),
        }),
        ('Anexos', {
            'fields': ('arquivo_boleto', 'comprovante'),
        }),
        ('Notificacoes', {
            'fields': ('email_lembrete_enviado', 'email_recibo_enviado'),
            'classes': ('collapse',),
        }),
        ('Integracao Efi (Automatico)', {
            'fields': ('efi_charge_id', 'efi_pix_txid', 'efi_boleto_url', 'efi_qrcode_pix'),
            'classes': ('collapse',),
            'description': 'Preenchidos automaticamente quando integrado com a Efi.',
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
