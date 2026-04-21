import json

from django import forms
from django.core.exceptions import ValidationError

from .models import Parameter


class ParameterAdminForm(forms.ModelForm):
    """
    Superusers may supply plaintext JSON once; it is encrypted into encrypted_payload on save.
    """

    plaintext_secrets_json = forms.CharField(
        label="Secrets (JSON object)",
        widget=forms.Textarea(attrs={"rows": 6, "cols": 80}),
        required=False,
        help_text=(
            "Optional. Paste a JSON object with sensitive keys, e.g. "
            '{"mm_url": "https://mm.example.com", "admin_token": "..."}. '
            "Stored encrypted at rest. Leave blank to keep existing ciphertext unchanged."
        ),
    )
    clear_encrypted_secrets = forms.BooleanField(
        label="Clear encrypted secrets",
        required=False,
        initial=False,
        help_text="Remove ciphertext for this row (irreversible without a DB backup).",
    )

    class Meta:
        model = Parameter
        exclude = ("encrypted_payload",)

    def __init__(self, *args, request_user=None, **kwargs):
        self.request_user = request_user
        super().__init__(*args, **kwargs)
        if not (request_user and request_user.is_superuser):
            self.fields.pop("plaintext_secrets_json", None)
            self.fields.pop("clear_encrypted_secrets", None)

    def clean(self):
        cleaned = super().clean()
        if not (self.request_user and self.request_user.is_superuser):
            return cleaned
        raw = (cleaned.get("plaintext_secrets_json") or "").strip()
        if raw and cleaned.get("clear_encrypted_secrets"):
            raise ValidationError(
                "Cannot both supply new secrets JSON and clear encrypted secrets in the same save."
            )
        if raw:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                self.add_error("plaintext_secrets_json", "Invalid JSON.")
                return cleaned
            if not isinstance(data, dict):
                self.add_error("plaintext_secrets_json", "Root value must be a JSON object.")
        return cleaned
