"""
About page view for PolySaaS
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from dose.utils import get_current_tenant, get_tenant_theme_colors
from dose.models import UserProfile


@login_required
def about_page(request):
    """
    About page for PolySaaS
    Shows information about the platform with same header as landing page
    """
    current_tenant = get_current_tenant(request)
    user_profile = UserProfile.objects.filter(user=request.user).first() if request.user.is_authenticated else None

    theme_info = {
        'name': 'tech_blue',
        'display_name': 'Tech Blue'
    }
    theme_colors = get_tenant_theme_colors('tech_blue')

    context = {
        'current_tenant': current_tenant,
        'user_profile': user_profile,
        'theme_info': theme_info,
        'theme_colors': theme_colors,
        'page_title': 'About PolySaaS'
    }

    return render(request, 'dose/about.html', context)

