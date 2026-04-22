"""
Case-insensitive username authentication backend.

Usernames are stored as-entered but looked up with iexact so that
'michael.oliver@polysaas.online' and 'Michael.Oliver@PolySaaS.online'
both authenticate to the same account. Password remains case-sensitive.

Django admin's single "Username" field often receives an email; when
``USERNAME_FIELD`` lookup fails, we fall back to ``email__iexact`` if the
user model has an ``email`` field.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class CaseInsensitiveModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD, "")
        username = (username or "").strip()

        user = self._get_user_by_iexact_field(UserModel, UserModel.USERNAME_FIELD, username)
        if user is None and hasattr(UserModel, "email"):
            user = self._get_user_by_iexact_field(UserModel, "email", username)

        if user is None:
            UserModel().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    @staticmethod
    def _get_user_by_iexact_field(UserModel, field: str, value: str):
        if not value:
            return None
        try:
            return UserModel.objects.get(**{f"{field}__iexact": value})
        except UserModel.DoesNotExist:
            return None
        except UserModel.MultipleObjectsReturned:
            return (
                UserModel.objects.filter(**{field: value})
                .filter(is_active=True)
                .first()
            )
