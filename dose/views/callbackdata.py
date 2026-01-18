from django.http import HttpResponse, Http404
from dose.models.callback_data import CallBackData

def callbackdata_view(request, id):
    try:
        cb = CallBackData.objects.get(id=id)
        html = cb.callbackdata.get('html', '') if cb.callbackdata else ''
        return HttpResponse(html, content_type='text/html')
    except CallBackData.DoesNotExist:
        raise Http404('Callback data not found')
