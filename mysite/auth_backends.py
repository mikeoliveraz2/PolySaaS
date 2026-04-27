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
        print(f"[DEBUG] >>> ENTER CaseInsensitiveModelBackend.authenticate: username={username}, password={'***' if password else None}, kwargs={kwargs}")
        print(f"[DEBUG] CaseInsensitiveModelBackend.authenticate called: username={username}, password={'***' if password else None}, kwargs={kwargs}")
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD, "")
        username = (username or "").strip()
        print(f"[DEBUG] Normalized username: '{username}'")

        user = self._get_user_by_iexact_field(UserModel, UserModel.USERNAME_FIELD, username)
        print(f"[DEBUG] User found by username: {user}")
        if user is None and hasattr(UserModel, "email"):
            user = self._get_user_by_iexact_field(UserModel, "email", username)
            print(f"[DEBUG] User found by email: {user}")

        if user is None:
            UserModel().set_password(password)
            print(f"[DEBUG] No user found for username/email: '{username}'")
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            print(f"[DEBUG] Authenticated user: {user}")
            return user
        print(f"[DEBUG] Password check failed or user cannot authenticate: {user}, password correct: {user.check_password(password) if user else 'n/a'}")
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
