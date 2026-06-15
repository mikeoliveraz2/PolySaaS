from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from dose.models.callback_data import CallBackData

def callbackdata_view(request, id):
    try:
        cb = CallBackData.objects.get(id=id)
        html = cb.callbackdata.get('html', '') if cb.callbackdata else ''
        return HttpResponse(html, content_type='text/html')
    except CallBackData.DoesNotExist:
        raise Http404('Callback data not found')


@login_required
def callback_log_viewer(request):
    """
    Admin dashboard: browse recent CallBackData, RequestLog, and ErrorLog
    entries with filtering, pagination, and AI-powered summary.
    """
    from dose.models.request_log import RequestLog, ErrorLog
    from dose.utils import get_current_tenant

    tenant = get_current_tenant(request)
    tenant_id = tenant.id if tenant else None
    schema_name = tenant.schema_name if tenant else 'public'

    # ── Filters ──
    days = int(request.GET.get('days', 7))
    event_key = request.GET.get('event_key', '').strip()
    model_filter = request.GET.get('model', '').strip().lower()
    since = timezone.now() - timedelta(days=days)

    # ── Query CallBackData ──
    cb_qs = CallBackData.objects.filter(pub_date__gte=since)
    if tenant_id:
        cb_qs = cb_qs.filter(tenant_id=tenant_id)
    if event_key:
        cb_qs = cb_qs.filter(matchingEventKey__icontains=event_key)
    cb_qs = cb_qs.order_by('-pub_date')

    # ── Query RequestLog ──
    req_qs = RequestLog.objects.filter(timestamp__gte=since)
    if tenant_id:
        req_qs = req_qs.filter(tenant_id=tenant_id)
    if event_key:
        req_qs = req_qs.filter(path__icontains=event_key)
    req_qs = req_qs.order_by('-timestamp')

    # ── Query ErrorLog ──
    err_qs = ErrorLog.objects.filter(timestamp__gte=since)
    if tenant_id:
        err_qs = err_qs.filter(tenant_id=tenant_id)
    err_qs = err_qs.order_by('-timestamp')

    # ── Paginate ──
    cb_page = Paginator(cb_qs, 20).get_page(request.GET.get('cb_page'))
    req_page = Paginator(req_qs, 20).get_page(request.GET.get('req_page'))
    err_page = Paginator(err_qs, 20).get_page(request.GET.get('err_page'))

    # ── Stats ──
    stats = {
        'callback_count': cb_qs.count(),
        'request_count': req_qs.count(),
        'error_count': err_qs.count(),
        'days': days,
        'tenant_name': tenant.name if tenant else 'All Tenants',
    }

    # ── AI Summary (optional, best-effort) ──
    ai_summary = None
    if request.GET.get('ai_summary') and cb_qs.count():
        try:
            from llm_router.providers import complete_chat
            from llm_router.router import route
            recent = list(cb_qs.values('matchingEventKey', 'description', 'pub_date')[:10])
            prompt = (
                "Summarize the following callback/activity log entries in 2-3 sentences. "
                "Highlight patterns, anomalies, or anything worth attention:\n\n"
                + "\n".join(
                    f"- {r['matchingEventKey'] or 'N/A'}: {r['description']} @ {r['pub_date']}"
                    for r in recent
                )
            )
            plan = route(prompt=prompt, user_tier="staff")
            ai_summary = complete_chat(
                plan,
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a concise DevOps assistant. Summarize logs. Keep it under 40 words.",
                max_tokens=256,
            )
        except Exception:
            ai_summary = None

    return render(request, 'dose/callback_log_viewer.html', {
        'cb_page': cb_page,
        'req_page': req_page,
        'err_page': err_page,
        'stats': stats,
        'ai_summary': ai_summary,
        'event_key_filter': event_key,
        'days_filter': days,
        'tenant': tenant,
        'schema_name': schema_name,
    })
