from django.contrib import admin
from .models import AuditLog, TerminalDevice


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'actor', 'action', 'target_type', 'target_id')
    list_filter = ('action', 'target_type', 'created_at')
    search_fields = ('description', 'target_type', 'target_id', 'actor__username')
    readonly_fields = ('created_at',)


@admin.register(TerminalDevice)
class TerminalDeviceAdmin(admin.ModelAdmin):
    list_display = (
        'terminal_name',
        'terminal_id',
        'preferred_print_mode',
        'auto_print',
        'is_active',
        'last_seen_user',
        'last_seen_at',
    )
    list_filter = ('preferred_print_mode', 'auto_print', 'is_active', 'last_seen_at')
    search_fields = ('terminal_name', 'terminal_id', 'last_seen_user__username')
    readonly_fields = ('created_at', 'updated_at', 'last_seen_at')