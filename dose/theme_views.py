from dose.models import UserProfile
from dose.tenant_utils import get_current_tenant
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json

@login_required
def toggle_theme(request):
    """
    Toggle between light and dark mode.
    Stores preference in session and cookie (not database - follows user across requests).
    """
    # Get user's preferred themes from session or defaults
    light_theme = request.session.get('light_theme', 'flatly')
    dark_theme = request.session.get('dark_theme', 'darkly')

    # Get current mode from session, cookie, or default to light
    current_mode = request.session.get('display_mode', 'light')
    # Also check cookie for persistence across sessions
    if 'display_mode' in request.COOKIES:
        current_mode = request.COOKIES.get('display_mode', 'light')

    dark_themes = ['darkly', 'cyborg', 'slate', 'superhero', 'solar']

    # Toggle logic: if currently dark, switch to light; else switch to dark
    if current_mode == 'dark' or (current_mode in dark_themes):
        new_mode = 'light'
        new_theme = light_theme
    else:
        new_mode = 'dark'
        new_theme = dark_theme

    # Store in session
    request.session['display_mode'] = new_mode

    # Build response with cookie
    response = JsonResponse({'theme': new_theme, 'mode': new_mode})
    response.set_cookie('display_mode', new_mode, max_age=31536000, path='/')  # 1 year

    return response

@login_required
@require_POST
def set_theme(request):
    tenant = get_current_tenant(request)
    if not tenant:
        return JsonResponse({'error': 'No tenant found for this session.'}, status=400)
    body = request.body.decode('utf-8').strip()
    data = {}
    if body:
        try:
            data = json.loads(body)
        except Exception as e:
            return JsonResponse({'error': f'JSON decode error: {e}'}, status=400)
    theme = data.get('theme')
    if not theme:
        return JsonResponse({'error': 'No theme provided.'}, status=400)
    profile, _ = UserProfile.objects.get_or_create(user=request.user, tenant=tenant)
    profile.theme = theme
    profile.save()
    return JsonResponse({'theme': profile.theme})
