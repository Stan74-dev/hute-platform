from django.contrib import admin
from .models import Branch, BranchTerminal

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "manager_name", "is_active", "created_at")
    search_fields = ("name", "code", "manager_name")
    list_filter = ("is_active",)

@admin.register(BranchTerminal)
class BranchTerminalAdmin(admin.ModelAdmin):
    list_display = ("terminal_name", "terminal_code", "branch", "is_active", "last_seen_at")
    search_fields = ("terminal_name", "terminal_code")
    list_filter = ("is_active", "branch")
