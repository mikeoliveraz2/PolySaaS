from django.http import HttpResponse
from django.shortcuts import render

def test_nextcloud_iframe(request):
    """Test view to verify NextCloud iframe embedding works"""
    html = '''<!DOCTYPE html>
<html>
<head>
    <title>NextCloud Iframe Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        iframe { border: 1px solid #ccc; }
    </style>
</head>
<body>
    <h1>NextCloud Iframe Test</h1>
    <p>This page tests if NextCloud can be embedded as an iframe through the Django passthrough middleware.</p>
    <iframe src="/admin/nextcloud/" width="100%" height="600px" frameborder="1">
        Your browser doesn't support iframes.
    </iframe>
</body>
</html>'''
    return HttpResponse(html)