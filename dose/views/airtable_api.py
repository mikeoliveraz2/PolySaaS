"""
Airtable API Views
Handles modal form submissions for posting to Airtable
"""
import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from allauth.socialaccount.models import SocialToken
# from dose.services.airtable_service import AirtablePostService  # Removed - airtable not used


@login_required
@require_http_methods(["POST"])
@csrf_protect
def airtable_post_api(request):
    """
    API endpoint for posting records to Airtable via modal form.
    Expects:
    - table_id: Airtable table ID (from form)
    - fields: JSON string with field data
    Returns:
    - {'success': bool, 'record_id': str, 'error': str}
    """
    try:
        # Get parameters from POST
        table_id = request.POST.get('table_id', '')
        fields_json = request.POST.get('fields', '{}')

        if not table_id:
            return JsonResponse({
                'success': False,
                'error': 'table_id is required'
            }, status=400)

        try:
            fields = json.loads(fields_json)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON in fields'
            }, status=400)

        # Get OAuth token
        try:
            token_obj = SocialToken.objects.get(
                account__user=request.user,
                account__provider='airtable'
            )
            oauth_token = token_obj.token
        except SocialToken.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'No Airtable OAuth token found. Please connect your Airtable account.'
            }, status=401)

        # Call Airtable API
        import requests
        url = f"https://api.airtable.com/v0/{AirtablePostService.BASE_ID}/{table_id}"
        headers = {
            'Authorization': f'Bearer {oauth_token}',
            'Content-Type': 'application/json'
        }
        payload = {
            'records': [
                {
                    'fields': fields
                }
            ]
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            data = response.json()
            record_id = data.get('records', [{}])[0].get('id', 'unknown')
            return JsonResponse({
                'success': True,
                'record_id': record_id,
                'message': 'Record created successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'Airtable API error: {response.status_code} - {response.text}'
            }, status=response.status_code)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)
