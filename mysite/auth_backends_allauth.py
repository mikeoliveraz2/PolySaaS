print("[DEBUG] AllauthCaseInsensitiveBackend module loaded")
from allauth.account.auth_backends import AuthenticationBackend
from mysite.auth_backends import CaseInsensitiveModelBackend
from django.contrib.auth import get_user_model

class AllauthCaseInsensitiveBackend(AuthenticationBackend):
    """
    Allauth backend that supports case-insensitive username/email authentication.
    """
    def authenticate(self, request, **credentials):
        print("[DEBUG] >>> ENTER AllauthCaseInsensitiveBackend.authenticate", credentials)
        User = get_user_model()
        username = credentials.get('username') or credentials.get('login') or credentials.get('email')
        password = credentials.get('password')

        if not username or not password:
            print("[DEBUG] Missing username/login/email or password in credentials", credentials)
            return None

        # Try case-insensitive username lookup
        user = User.objects.filter(username__iexact=username).first()
        if not user:
            # Try case-insensitive email lookup
            user = User.objects.filter(email__iexact=username).first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            print(f"[DEBUG] Authenticated user: {user}")
            return user

        print(f"[DEBUG] No matching user for username/email: {username}")
        return None
