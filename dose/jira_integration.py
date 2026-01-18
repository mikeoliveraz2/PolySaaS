"""
Jira Integration Views for DOSE
Handles API calls to external Jira instance while maintaining DOSE context
"""
import requests
import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)

# Jira API configuration
JIRA_BASE_URL = 'https://mikeoliveraz.atlassian.net'
JIRA_API_URL = f'{JIRA_BASE_URL}/rest/api/3'

@login_required
def jira_home(request):
    """
    Handle requests to /jira/home by fetching data from Jira API
    and returning it within DOSE context
    """
    try:
        # Example: Get current user's Jira profile or dashboard data
        jira_url = f'{JIRA_API_URL}/myself'
        
        # You'll need to add authentication headers here
        # For now, we'll return a placeholder response
        
        response_data = {
            'status': 'success',
            'message': 'Jira integration active',
            'dose_user': request.user.username if request.user.is_authenticated else 'anonymous',
            'jira_endpoint': jira_url,
            'context': 'DOSE application with Jira integration',
            'available_endpoints': [
                '/jira/home',
                '/jira/projects',
                '/jira/issues',
                '/jira/boards'
            ]
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error in jira_home: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Jira integration error: {str(e)}',
            'dose_context': 'maintained'
        }, status=500)

@login_required  
def jira_projects(request):
    """
    Fetch Jira projects via API while maintaining DOSE context
    """
    try:
        # Placeholder for actual Jira API call
        response_data = {
            'status': 'success',
            'message': 'Jira projects endpoint',
            'dose_user': request.user.username,
            'data': 'Projects data would go here'
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error in jira_projects: {str(e)}")
        return JsonResponse({
            'status': 'error', 
            'message': str(e)
        }, status=500)

@login_required
def jira_issues(request):
    """
    Fetch Jira issues via API while maintaining DOSE context
    """
    try:
        # Placeholder for actual Jira API call
        response_data = {
            'status': 'success',
            'message': 'Jira issues endpoint',
            'dose_user': request.user.username,
            'data': 'Issues data would go here'
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error in jira_issues: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def jira_proxy_generic(request, path):
    """
    Generic proxy for any Jira path while maintaining DOSE context
    """
    try:
        # Log the request for debugging
        logger.info(f"Jira proxy request: {request.method} /jira/{path}")
        
        response_data = {
            'status': 'success',
            'message': f'Jira proxy for path: {path}',
            'method': request.method,
            'dose_context': 'maintained',
            'user': request.user.username if request.user.is_authenticated else 'anonymous',
            'original_path': f'/jira/{path}',
            'note': 'This is a placeholder. Replace with actual Jira API calls.'
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error in jira_proxy_generic: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'dose_context': 'maintained'
        }, status=500)
