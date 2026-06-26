print("[DEBUG] AllauthCaseInsensitiveBackend module loaded")
from allauth.account.auth_backends import AuthenticationBackend
from django.contrib.auth import get_user_model

from mysite.admin_forms import register_admin_login_form

register_admin_login_form()


class AllauthCaseInsensitiveBackend(AuthenticationBackend):
    """
    Username/email lookup is case-insensitive (username__iexact / email__iexact).
    Password verification uses check_password() and remains case-sensitive.
    """
    def authenticate(self, request, **credentials):
        print("[DEBUG] >>> ENTER AllauthCaseInsensitiveBackend.authenticate", credentials, flush=True)
        User = get_user_model()
        username = credentials.get('username') or credentials.get('login') or credentials.get('email')
        password = credentials.get('password')

        if username is not None:
            username = str(username).strip()

        if not username or not password:
            print("[DEBUG] Missing username/login/email or password in credentials", credentials, flush=True)
            return None

        # Try case-insensitive username lookup
        user = User.objects.filter(username__iexact=username).first()
        if not user:
            # Try case-insensitive email lookup
            user = User.objects.filter(email__iexact=username).first()

        if not user:
            print(f"[DEBUG] No matching user for username/email: {username}", flush=True)
            return None

        if not user.check_password(password):
            print(f"[DEBUG] Password mismatch for user: {user}", flush=True)
            return None

        if not self.user_can_authenticate(user):
            print(f"[DEBUG] user_can_authenticate=False for user: {user}", flush=True)
            return None

        print(f"[DEBUG] Authenticated user: {user}", flush=True)
        return user
