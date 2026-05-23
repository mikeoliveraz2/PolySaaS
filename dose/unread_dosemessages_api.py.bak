# Moved from dose/views/unread_dosemessages_api.py

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from dose.models import DoseMessage

@login_required
def unread_dosemessages_api(request):
    user = request.user
    if request.method == 'POST':
        DoseMessage.objects.filter(user=user, is_read=False).update(is_read=True)
        return JsonResponse({'count': 0, 'messages': []})
    else:
        unread_messages = DoseMessage.objects.filter(user=user, is_read=False)
        count = unread_messages.count()
        messages = list(unread_messages.values('id', 'message', 'level', 'created_at'))
        return JsonResponse({'count': count, 'messages': messages})
