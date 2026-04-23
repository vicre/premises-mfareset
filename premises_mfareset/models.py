from django.conf import settings
from django.db import models


class MfaResetAuditLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mfa_reset_audit_logs",
    )

    actor_upn = models.CharField(max_length=255, blank=True)
    target_upn = models.CharField(max_length=255, blank=True)
    target_display_name = models.CharField(max_length=255, blank=True)
    target_ou = models.CharField(max_length=255, blank=True)

    allowed_ous = models.TextField(blank=True)
    status_code = models.PositiveIntegerField()
    success = models.BooleanField(default=False)

    message = models.TextField(blank=True)

    list_methods_payload = models.JSONField(null=True, blank=True)
    prepared_methods_payload = models.JSONField(null=True, blank=True)
    reset_result_payload = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "MFA reset audit log"
        verbose_name_plural = "MFA reset audit logs"

    def __str__(self) -> str:
        return f"{self.created_at:%Y-%m-%d %H:%M:%S} | {self.actor_upn} -> {self.target_upn} | {self.status_code}"