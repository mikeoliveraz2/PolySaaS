from django.http import JsonResponse
from dose.models import DoseMessage
from django.contrib.auth.decorators import login_required
import logging

logger = logging.getLogger(__name__)

@login_required
def unread_dosemessages_api(request):
    logger.info(f"unread_dosemessages_api called: method={request.method}, user={getattr(request.user, 'username', None)}, is_superuser={getattr(request.user, 'is_superuser', None)}")
    # PATCHED: Only assign DoseMessage.user if request.user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({'unread_messages': [], 'count': 0})
    # POST: Mark all unread messages as read
    if request.method == 'POST':
        logger.info("POST request to mark messages as read")
        if request.user.is_superuser:
            updated = DoseMessage.objects.filter(is_read=False).update(is_read=True)
            logger.info(f"Marked {updated} messages as read (superuser)")
        else:
            updated = DoseMessage.objects.filter(is_read=False, user=request.user).update(is_read=True)
            logger.info(f"Marked {updated} messages as read for user {request.user}")
        return JsonResponse({'status': 'success', 'updated': updated})
    # GET: Return unread DoseMessages for the current user (or all if superuser)
    if request.user.is_superuser:
        messages = DoseMessage.objects.filter(is_read=False)
    else:
        messages = DoseMessage.objects.filter(is_read=False, user=request.user)
    logger.info(f"Returning {messages.count()} unread messages")
    data = [
        {
            'id': msg.id,
            'message': msg.message,
            'level': msg.level,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_read': msg.is_read,
            'user': msg.user.username if msg.user else None
        }
        for msg in messages
    ]
    return JsonResponse({'unread_messages': data, 'count': len(data)})
