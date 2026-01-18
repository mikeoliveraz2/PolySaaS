from allauth.account.views import LoginView

class CustomLoginView(LoginView):
    template_name = "account/login.html"
