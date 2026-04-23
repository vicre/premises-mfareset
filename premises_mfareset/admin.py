from django.contrib import admin
from .models import MfaResetAuditLog


@admin.register(MfaResetAuditLog)
class MfaResetAuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "actor_upn",
        "target_upn",
        "target_ou",
        "status_code",
        "success",
    )
    list_filter = ("success", "status_code", "target_ou", "created_at")
    search_fields = ("actor_upn", "target_upn", "target_display_name", "message")
    readonly_fields = (
        "created_at",
        "actor",
        "actor_upn",
        "target_upn",
        "target_display_name",
        "target_ou",
        "allowed_ous",
        "status_code",
        "success",
        "message",
        "list_methods_payload",
        "prepared_methods_payload",
        "reset_result_payload",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False