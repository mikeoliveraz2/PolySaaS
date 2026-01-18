from dose.models import UserProfile
from dose.tenant_utils import get_current_tenant
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json

@login_required
def toggle_theme(request):
    tenant = get_current_tenant(request)
    if not tenant:
        return JsonResponse({'error': 'No tenant found for this session.'}, status=400)
    profile, _ = UserProfile.objects.get_or_create(user=request.user, tenant=tenant)
    # Use user's preferred light/dark theme for toggling
    current_theme = getattr(profile, 'last_selected_theme', 'flatly')
    light_theme = getattr(profile, 'light_theme', 'flatly')
    dark_theme = getattr(profile, 'dark_theme', 'darkly')
    dark_themes = ['darkly', 'cyborg', 'slate', 'superhero', 'solar']
    # If current theme is a dark theme, switch to light; else switch to dark
    if current_theme in dark_themes:
        new_theme = light_theme
    else:
        new_theme = dark_theme
    # Only update last_selected_theme, do NOT overwrite light_theme or dark_theme
    profile.last_selected_theme = new_theme
    profile.save()
    return JsonResponse({'theme': new_theme})

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
