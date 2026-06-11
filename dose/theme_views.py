# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Font and Theme Toggle — 2026-06-11 — documentation/BINGO_FONT_AND_THEME_TOGGLE_2026-06-11.md
from dose.models import UserProfile
from dose.tenant_utils import get_current_tenant
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json

LIGHT_THEME_DEFAULT = 'sandstone'
DARK_THEME_DEFAULT = 'darkly'


def _profile_theme_prefs(request):
    """Saved Bootswatch picks from UserProfile (palette), with sane defaults."""
    light_theme = request.session.get('light_theme') or LIGHT_THEME_DEFAULT
    dark_theme = request.session.get('dark_theme') or DARK_THEME_DEFAULT
    tenant = get_current_tenant(request)
    if tenant and request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user, tenant=tenant)
            light_theme = profile.light_theme or light_theme
            dark_theme = profile.dark_theme or dark_theme
        except UserProfile.DoesNotExist:
            pass
    request.session['light_theme'] = light_theme
    request.session['dark_theme'] = dark_theme
    return light_theme, dark_theme


def _display_mode_response(request, mode, light_theme, dark_theme):
    new_theme = light_theme if mode == 'light' else dark_theme
    request.session['display_mode'] = mode
    response = JsonResponse({'theme': new_theme, 'mode': mode})
    response.set_cookie('display_mode', mode, max_age=31536000, path='/')
    return response


@login_required
def toggle_theme(request):
    """
    Flip light ↔ dark only. Bootswatch theme names come from UserProfile (palette).
    """
    light_theme, dark_theme = _profile_theme_prefs(request)

    # Get current mode from session, cookie, or default to light
    current_mode = request.session.get('display_mode', 'light')
    # Also check cookie for persistence across sessions
    if 'display_mode' in request.COOKIES:
        current_mode = request.COOKIES.get('display_mode', 'light')

    # Toggle logic: if currently dark, switch to light; else switch to dark
    if current_mode == 'dark':
        new_mode = 'light'
    else:
        new_mode = 'dark'

    request.session['theme_mode_pref'] = new_mode
    return _display_mode_response(request, new_mode, light_theme, dark_theme)


@login_required
def set_display_mode(request):
    """
    Set display mode explicitly: light, dark, or system (client passes effective light|dark).
    Does not change Bootswatch theme picks — use the palette / select-theme for that.
    """
    mode = (request.GET.get('mode') or request.POST.get('mode') or '').strip().lower()
    if mode not in ('light', 'dark', 'system'):
        return JsonResponse({'error': 'mode must be light, dark, or system'}, status=400)

    light_theme, dark_theme = _profile_theme_prefs(request)

    if mode == 'system':
        effective = (request.GET.get('effective') or request.POST.get('effective') or 'light').strip().lower()
        if effective not in ('light', 'dark'):
            effective = 'light'
        request.session['theme_mode_pref'] = 'system'
        response = _display_mode_response(request, effective, light_theme, dark_theme)
        response.set_cookie('ps_theme_mode', 'system', max_age=31536000, path='/')
        return response

    request.session['theme_mode_pref'] = mode
    response = _display_mode_response(request, mode, light_theme, dark_theme)
    response.set_cookie('ps_theme_mode', mode, max_age=31536000, path='/')
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
