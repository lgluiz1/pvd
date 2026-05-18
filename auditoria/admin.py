from django.contrib import admin
from auditoria.models import LogAuditoria
@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ['acao', 'usuario', 'empresa', 'created_at']
    list_filter = ['acao', 'empresa']
