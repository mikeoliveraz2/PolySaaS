"""
API endpoint for unread notifications
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from dose.models import DoseMessage

@login_required
def get_unread_notifications(request):
    """
    Return count of unread notifications for the current user
    Used by the notification bell in admin navbar
    """
    try:
        # Get unread messages count
        unread_count = DoseMessage.objects.filter(
            user=request.user,
            is_read=False
        ).count()

        # Get recent unread messages for dropdown
        recent_notifications = DoseMessage.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')[:5]

        notifications_data = []
        for msg in recent_notifications:
            notifications_data.append({
                'id': msg.id,
                'subject': msg.message[:50] if len(msg.message) > 50 else msg.message,
                'preview': msg.message[:100] if msg.message else '',
                'created_at': msg.created_at.isoformat() if msg.created_at else None,
                'level': msg.level
            })

        return JsonResponse({
            'success': True,
            'unread_count': unread_count,
            'notifications': notifications_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'unread_count': 0,
            'notifications': []
        })
