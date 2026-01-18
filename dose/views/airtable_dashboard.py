"""
Airtable Dashboard View
Displays Airtable records (tickets synced from osTicket) in a pretty Django admin interface
"""
import requests
import json
from typing import Dict, Optional, List
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from allauth.socialaccount.models import SocialToken


@login_required
def airtable_tickets_view(request):
    """
    Display Airtable records as a dashboard table in Django admin style.
    Fetches from Airtable API using OAuth token.
    """
    base_id = "apphVcCZHGhbpVOa4"
    table_id = "tblZOaYYkBQdJZshL"  # Tickets table

    tickets = []
    error_message = None

    try:
        # Get OAuth token
        token_obj = SocialToken.objects.get(
            account__user=request.user,
            account__provider='airtable'
        )
        oauth_token = token_obj.token
    except SocialToken.DoesNotExist:
        error_message = "No Airtable OAuth token found. Please connect your Airtable account in settings."
        return render(request, 'admin/airtable_tickets_dashboard.html', {
            'tickets': [],
            'error_message': error_message,
            'user': request.user
        })
    except Exception as e:
        error_message = f"Error retrieving OAuth token: {str(e)}"
        return render(request, 'admin/airtable_tickets_dashboard.html', {
            'tickets': [],
            'error_message': error_message,
            'user': request.user
        })

    try:
        # Fetch records from Airtable
        url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
        headers = {
            'Authorization': f'Bearer {oauth_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            records = data.get('records', [])

            # Transform records into displayable format
            for record in records:
                ticket = {
                    'id': record.get('id'),
                    'fields': record.get('fields', {}),
                    'created_time': record.get('createdTime', ''),
                }
                tickets.append(ticket)
        else:
            error_message = f"Airtable API error: {response.status_code} - {response.text[:200]}"

    except requests.exceptions.Timeout:
        error_message = "Request to Airtable timed out. Please try again."
    except requests.exceptions.RequestException as e:
        error_message = f"Error fetching from Airtable: {str(e)}"
    except json.JSONDecodeError as e:
        error_message = f"Invalid JSON response from Airtable: {str(e)}"
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"

    return render(request, 'admin/airtable_tickets_dashboard.html', {
        'tickets': tickets,
        'error_message': error_message,
        'user': request.user,
        'base_id': base_id,
        'table_id': table_id
    })


@login_required
def airtable_tickets_api(request):
    """
    API endpoint to fetch Airtable tickets as JSON.
    Used for AJAX refresh.
    """
    base_id = "apphVcCZHGhbpVOa4"
    table_id = "tblZOaYYkBQdJZshL"

    try:
        token_obj = SocialToken.objects.get(
            account__user=request.user,
            account__provider='airtable'
        )
        oauth_token = token_obj.token
    except SocialToken.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'No Airtable OAuth token'
        }, status=401)

    try:
        url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
        headers = {
            'Authorization': f'Bearer {oauth_token}',
            'Content-Type': 'application/json'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            records = data.get('records', [])
            return JsonResponse({
                'success': True,
                'records': records
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'Airtable API error: {response.status_code}'
            }, status=response.status_code)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
