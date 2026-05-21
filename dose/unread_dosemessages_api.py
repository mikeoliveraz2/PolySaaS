from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from dose.models import DoseMessage
import json

@login_required
@require_http_methods(["GET", "POST", "PATCH"])
def unread_dosemessages_api(request):
    """
    API endpoint for managing unread DOSE messages.
    
    GET: Return list of unread messages for the current user
    POST: Mark all unread messages as read
    PATCH: Mark a specific message as read (requires message_id in body)
    """
    user = request.user
    
    if request.method == 'PATCH':
        # Mark a specific message as read
        try:
            body = json.loads(request.body)
            message_id = body.get('message_id')
            if not message_id:
                return JsonResponse({'error': 'message_id required'}, status=400)
            
            # Update the specific message
            updated = DoseMessage.objects.filter(
                id=message_id, 
                user=user, 
                is_read=False
            ).update(is_read=True)
            
            # Return updated count
            unread_count = DoseMessage.objects.filter(user=user, is_read=False).count()
            return JsonResponse({
                'success': updated > 0,
                'updated': updated,
                'count': unread_count
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    elif request.method == 'POST':
        # Mark all unread messages as read
        updated = DoseMessage.objects.filter(user=user, is_read=False).update(is_read=True)
        return JsonResponse({
            'count': 0,
            'messages': [],
            'updated': updated
        })
    
    else:  # GET
        # Return unread messages
        unread_messages = DoseMessage.objects.filter(user=user, is_read=False)
        count = unread_messages.count()
        messages = list(unread_messages.values('id', 'message', 'level', 'created_at'))
        return JsonResponse({'count': count, 'messages': messages})