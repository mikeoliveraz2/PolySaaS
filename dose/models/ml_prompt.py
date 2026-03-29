from django.db import models

from .tenant_aware_model import TenantAwareModel


class MLPrompt(TenantAwareModel):
    """
    Tenant-scoped named prompts (e.g. for LLM / agent templates).
    Lookup by `key` within a tenant; `matchingEventKey` on other ML rows can reference the same key string.
    """

    id = models.BigAutoField(primary_key=True)
    key = models.CharField(
        max_length=150,
        help_text="Stable identifier for code or orchestration (unique per tenant).",
    )
    description = models.CharField(max_length=255, default="Description")
    prompt_text = models.TextField(help_text="Full prompt body.")

    class Meta:
        verbose_name = "ML prompt"
        verbose_name_plural = "ML prompts"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "key"],
                name="dose_mlprompt_unique_tenant_key",
            ),
        ]

    def __str__(self):
        return f"{self.key} — {self.description[:40]}"
