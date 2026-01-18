#!/usr/bin/env python
"""
Simple test middleware that bypasses all complexity
"""
from django.http import HttpResponse
import requests
import logging

logger = logging.getLogger(__name__)

class SimplePassthroughMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.process_request(request)
        if response:
            return response
        return self.get_response(request)

    def process_request(self, request):
        if request.path.startswith('/dose/osticket/'):
            logger.info(f"[SIMPLE] Processing: {request.path}")
            
            try:
                # Make simple request to external service
                external_response = requests.get('https://demozone.surpaascompaas.com/surpaas/')
                
                logger.info(f"[SIMPLE] External status: {external_response.status_code}")
                logger.info(f"[SIMPLE] External content-type: {external_response.headers.get('content-type')}")
                logger.info(f"[SIMPLE] External content length: {len(external_response.content)} bytes")
                
                # Create Django response with the exact content from requests
                response = HttpResponse(
                    content=external_response.text,  # Let requests handle all decompression
                    status=external_response.status_code,
                    content_type=external_response.headers.get('content-type', 'text/html')
                )
                
                logger.info(f"[SIMPLE] Django response created with {len(response.content)} bytes")
                return response
                
            except Exception as e:
                logger.error(f"[SIMPLE] Error: {e}")
                return HttpResponse(f"<h1>Error</h1><p>{e}</p>", status=500)
        
        return None