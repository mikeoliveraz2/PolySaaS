import json

from django.contrib import admin, messages
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse

from .forms import ParameterAdminForm
from .models import Parameter


@admin.display(description="Secrets")
def _secrets_badge(obj):
    if obj.pk and obj.has_encrypted_secrets():
        return "Encrypted"
    return "—"


class ParameterAdmin(admin.ModelAdmin):
    """
    Staff see Parameter rows without ciphertext. Superusers manage encrypted secrets
    via the Secrets (JSON) field; ciphertext is never shown as plaintext in admin.
    """

    form = ParameterAdminForm
    fieldsets = [
        ("Basic Information", {"fields": ["matchingKey", "sequence", "description"]}),
        (
            "Parameter Values",
            {
                "fields": [
                    "param1",
                    "param2",
                    "param3",
                    "param4",
                    "param5",
                    "param6",
                    "param7",
                    "param8",
                    "param9",
                    "param10",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Advanced Configuration",
            {
                "fields": ["param_kwargs_json"],
                "classes": ["collapse"],
                "description": "JSON data for additional configuration parameters",
            },
        ),
        (
            "Encrypted secrets (superuser)",
            {
                "fields": ["plaintext_secrets_json", "clear_encrypted_secrets", "encrypted_status"],
                "classes": ["collapse"],
                "description": "Sensitive values are stored with Fernet encryption. "
                "Ciphertext is never displayed here.",
            },
        ),
        (
            "Audit Information",
            {
                "fields": ["created_by", "created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    list_display = ("matchingKey", "sequence", "description", _secrets_badge, "created_at", "created_by")
    list_filter = ["created_at", "sequence", "created_by"]
    search_fields = ["matchingKey", "description", "param1", "param2", "param3"]
    readonly_fields = ["created_at", "updated_at"]
    list_per_page = 25

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(Q(encrypted_payload__isnull=True) | Q(encrypted_payload=""))

    def get_fieldsets(self, request, obj=None):
        fs = list(super().get_fieldsets(request, obj))
        if not request.user.is_superuser:
            fs = [b for b in fs if b[0] != "Encrypted secrets (superuser)"]
        return fs

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if request.user.is_superuser:
            ro.append("encrypted_status")
        return ro

    def get_form(self, request, obj=None, **kwargs):
        form_class = super().get_form(request, obj, **kwargs)

        class BoundParameterForm(form_class):
            def __init__(self, *args, **inner):
                inner["request_user"] = request.user
                super().__init__(*args, **inner)

        return BoundParameterForm

    @admin.display(description="Encrypted payload")
    def encrypted_status(self, obj):
        if not obj or not obj.pk:
            return "—"
        if obj.has_encrypted_secrets():
            return f"Ciphertext present ({len(obj.encrypted_payload)} bytes)"
        return "None"

    def has_view_permission(self, request, obj=None):
        if obj is not None and obj.has_encrypted_secrets() and not request.user.is_superuser:
            return False
        return super().has_view_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.has_encrypted_secrets() and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.has_encrypted_secrets() and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        if request.user.is_superuser and hasattr(form, "cleaned_data"):
            if form.cleaned_data.get("clear_encrypted_secrets"):
                obj.encrypted_payload = None
            else:
                raw = (form.cleaned_data.get("plaintext_secrets_json") or "").strip()
                if raw:
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        self.message_user(
                            request,
                            "Secrets JSON was invalid; encrypted_payload not updated.",
                            level=messages.ERROR,
                        )
                    else:
                        if isinstance(data, dict):
                            from parameters.crypto import encrypt_json_dict

                            try:
                                obj.encrypted_payload = encrypt_json_dict(data)
                            except Exception as exc:
                                self.message_user(
                                    request,
                                    f"Could not encrypt secrets: {exc}",
                                    level=messages.ERROR,
                                )
                        else:
                            self.message_user(
                                request,
                                "Secrets root must be a JSON object.",
                                level=messages.ERROR,
                            )
        super().save_model(request, obj, form, change)

    def response_add(self, request, obj, post_url_override=None):
        if "_popup" in request.POST:
            return HttpResponseRedirect(reverse("admin:parameters_parameter_changelist"))
        return super().response_add(request, obj, post_url_override)

    def response_change(self, request, obj):
        if "_popup" in request.POST:
            return HttpResponseRedirect(reverse("admin:parameters_parameter_changelist"))
        return super().response_change(request, obj)


admin.site.register(Parameter, ParameterAdmin)
