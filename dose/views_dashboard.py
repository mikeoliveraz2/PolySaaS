from django.shortcuts import render
from django.http import HttpResponse

def dashboard_view(request):
    return HttpResponse("<h1>Welcome to your Dashboard!</h1><p>Subscription successful.</p>")
