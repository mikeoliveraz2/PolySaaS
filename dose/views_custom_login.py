from allauth.account.views import LoginView

class CustomLoginView(LoginView):
    template_name = "account/login.html"

    def dispatch(self, request, *args, **kwargs):
        print("[DEBUG] CustomLoginView.dispatch called")
        # TEMP HACK: Flatten list values in POST for login/password
        if request.method == "POST":
            mutable = request.POST._mutable
            request.POST._mutable = True
            for key in ("login", "password", "username"):
                val = request.POST.getlist(key)
                if isinstance(val, list) and len(val) == 1:
                    request.POST[key] = val[0]
            request.POST._mutable = mutable
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        from django.contrib.auth import authenticate, login
        credentials = form.cleaned_data.copy()
        # Flatten list values for login/password if present
        for key in ("login", "password", "username"):
            val = credentials.get(key)
            if isinstance(val, list) and len(val) == 1:
                credentials[key] = val[0]
        print("[DEBUG] CustomLoginView.form_valid called with:", credentials)
        print("[DEBUG] form.cleaned_data keys:", list(credentials.keys()))
        import django.conf
        print("[DEBUG] AUTHENTICATION_BACKENDS:", getattr(django.conf.settings, 'AUTHENTICATION_BACKENDS', None))
        # Pass both 'username' and 'login' to support allauth and custom backends
        user = authenticate(
            self.request,
            username=credentials.get('login') or credentials.get('username'),
            login=credentials.get('login'),
            password=credentials.get('password')
        )
        print("[DEBUG] authenticate() returned:", user)
        if user is not None:
            print("[DEBUG] User backend:", getattr(user, 'backend', None))
            login(self.request, user)
            print("[DEBUG] User logged in with backend:", getattr(user, 'backend', None))
            return super().form_valid(form)
        else:
            print("[DEBUG] authenticate() failed in CustomLoginView.form_valid")
            return self.form_invalid(form)

    def form_invalid(self, form):
        print("[DEBUG] CustomLoginView.form_invalid called. Errors:", form.errors)
        try:
            print("[DEBUG] form.cleaned_data (invalid):", getattr(form, 'cleaned_data', None))
            print("[DEBUG] form.data (raw):", dict(form.data))
            raw_login = None
            raw_password = None
            try:
                raw_login = self.request.POST.get('login') or self.request.POST.get('username')
                raw_password = self.request.POST.get('password')
            except Exception:
                raw_login = None
                raw_password = None

            if raw_login:
                try:
                    from django.contrib.auth import get_user_model, authenticate
                    User = get_user_model()
                    u_by_username = User.objects.filter(username__iexact=raw_login).first()
                    u_by_email = User.objects.filter(email__iexact=raw_login).first()
                    print("[DEBUG] raw_login:", raw_login)
                    print("[DEBUG] user(username__iexact) exists:", bool(u_by_username))
                    print("[DEBUG] user(email__iexact) exists:", bool(u_by_email))
                    u = u_by_username or u_by_email
                    if u is not None and raw_password is not None:
                        try:
                            print("[DEBUG] check_password() for matched user:", u.check_password(raw_password))
                            print("[DEBUG] matched user is_active/is_staff/is_superuser:", u.is_active, u.is_staff, u.is_superuser)
                        except Exception as e:
                            print("[DEBUG] check_password() raised:", e)

                    try:
                        auth_user = authenticate(
                            self.request,
                            username=raw_login,
                            login=raw_login,
                            password=raw_password,
                        )
                        print("[DEBUG] authenticate() during form_invalid returned:", auth_user)
                    except Exception as e:
                        print("[DEBUG] authenticate() during form_invalid raised:", e)
                except Exception as e:
                    print("[DEBUG] User existence/auth debug failed:", e)
        except Exception as e:
            print("[DEBUG] Exception printing form data:", e)
        return super().form_invalid(form)
