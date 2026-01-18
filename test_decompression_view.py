#!/usr/bin/env python
"""
Simple test view to check if content is properly decompressed
"""
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests

@csrf_exempt
def test_decompression(request):
    """Test view that returns decompressed content directly"""
    try:
        # Make direct request to external service
        external_response = requests.get('https://demozone.surpaascompaas.com/surpaas/')
        
        # Get decompressed text content
        text_content = external_response.text
        
        # Create response with explicit headers to prevent compression
        response = HttpResponse(
            content=text_content.encode('utf-8'),
            content_type='text/html; charset=utf-8'
        )
        
        # Aggressively prevent compression
        response['Content-Encoding'] = 'identity'
        response['Cache-Control'] = 'no-transform, no-cache'
        response['Pragma'] = 'no-cache'
        response['Vary'] = 'Accept-Encoding'
        
        return response
        
    except Exception as e:
        return HttpResponse(f"Error: {e}", status=500)

@csrf_exempt
def simple_html_test(request):
    """Simple HTML test to verify browser rendering"""
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Compression Test</title>
</head>
<body>
    <h1>This is a simple HTML test</h1>
    <p>If you can see this text clearly, then HTML rendering is working.</p>
    <p>If you see compressed/encoded characters, then there's a compression issue.</p>
    <p>Current time: ''' + str(request.META.get('HTTP_HOST', 'unknown')) + '''</p>
</body>
</html>'''
    
    response = HttpResponse(
        content=html_content,  # Pass as string, not bytes
        content_type='text/html; charset=utf-8'
    )
    
    # Prevent compression
    response['Content-Encoding'] = 'identity'
    response['Cache-Control'] = 'no-transform'
    
    return response

@csrf_exempt 
def external_direct_test(request):
    """Test direct external content without middleware complexity"""
    try:
        import requests
        
        # Get external content
        external_response = requests.get('https://demozone.surpaascompaas.com/surpaas/')
        
        # Return it directly as a string (not bytes)
        response = HttpResponse(
            content=external_response.text,  # Use .text property for automatic decompression
            content_type='text/html; charset=utf-8'
        )
        
        # Prevent any compression
        response['Content-Encoding'] = 'identity'
        response['Cache-Control'] = 'no-transform, no-cache'
        
        return response
        
    except Exception as e:
        return HttpResponse(f"<h1>Error</h1><p>{e}</p>", content_type='text/html')