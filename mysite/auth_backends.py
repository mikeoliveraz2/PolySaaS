"""
Case-insensitive username authentication backend.

Usernames are stored as-entered but looked up with iexact so that
'michael.oliver@polysaas.online' and 'Michael.Oliver@polysaas.online'
both authenticate to the same account. Password remains case-sensitive.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class CaseInsensitiveModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD, "")
        try:
            user = UserModel.objects.get(
                **{f"{UserModel.USERNAME_FIELD}__iexact": username}
            )
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            # If somehow two users match case-insensitively, fall through
            # so neither gets a free login — require exact match instead.
            return UserModel.objects.filter(
                **{UserModel.USERNAME_FIELD: username}
            ).filter(is_active=True).first() or None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
