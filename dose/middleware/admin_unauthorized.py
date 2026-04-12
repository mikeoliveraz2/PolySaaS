# Custom Unauthorized Middleware for Django Admin

from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin
from dose.middleware.debug import DebugStackMiddleware   # ← ADD THIS

class AdminUnauthorizedMiddleware(DebugStackMiddleware, MiddlewareMixin):  # ← FIRST!

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.path.startswith('/admin/')
            and request.user.is_authenticated
            and not (request.user.is_staff or request.user.is_superuser)
        ):
            return render(request, 'dose/unauthorized.html', status=403)
        return self.get_response(request)
