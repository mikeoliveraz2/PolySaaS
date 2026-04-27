# Page after successful subscribe: connect to Google or skip
def connect_social_after_subscribe(request):
    return render(request, 'dose/connect_social_after_subscribe.html')
# DO NOT MODIFY: Critical system file. Ask before making changes.
# Debug session view for inspecting session and user info
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
@login_required
def debug_session_view(request):
    """Debug view to inspect session and user info"""
    context = {
        'user': request.user,
        'session': dict(request.session.items()),
        'is_authenticated': request.user.is_authenticated,
        'session_keys': list(request.session.keys()),
    }
    return render(request, 'dose/debug_session.html', context)
# Bulk moved views from views.py
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import Http404, HttpResponseForbidden
from django.utils.safestring import mark_safe
from django.views.decorators.cache import never_cache
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from dose.models import (
    AtomicService,
    Subscription,
    UserProfile,
    UserTenantMembership,
    Tenant,
    RequestLog,
    ErrorLog,
)
from dose.tenant_fbv import require_tenant_membership_for_fbv, user_can_manage_tenant_settings
from dose.serializers import AtomicServiceSerializer, SubscriptionSerializer, RequestLogSerializer, ErrorLogSerializer
from django.conf import settings
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def debug_tenant_session(request):
    user = request.user
    session_keys = dict(request.session.items())
    # Add any debug logic needed
    return render(request, 'dose/debug_tenant.html', {'user': user, 'session_keys': session_keys})

def index(request):
    if not request.user.is_authenticated:
        login_url = f"/accounts/login/?next={request.path}"
        return redirect(login_url)
    context, response = _build_landing_page_context(request)
    if response is not None:
        return response
    return render(request, 'dose/user_dashboard.html', context)

def logout_view(request):
    """Basic logout view for Django with debug logging."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"logout_view: Logging out user {getattr(request.user, 'username', None)}. Session keys before logout: {list(request.session.keys())}")
    logout(request)
    logger.info(f"logout_view: Session keys after logout: {list(request.session.keys())}")
    return redirect('/')

class RequestLogViewSet(viewsets.ModelViewSet):
    queryset = RequestLog.objects.all()
    serializer_class = RequestLogSerializer
    permission_classes = [permissions.IsAdminUser]

class ErrorLogViewSet(viewsets.ModelViewSet):
    queryset = ErrorLog.objects.all()
    serializer_class = ErrorLogSerializer
    permission_classes = [permissions.IsAdminUser]

class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.AllowAny]
    def create(self, request, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        import json as pyjson
        print("SubscriptionViewSet.create called")
        print(f"Request content_type: {request.content_type}")
        # ...existing code...
# Custom swagger view moved from views.py
from django.shortcuts import render
def custom_swagger_view(request):
    return render(request, 'dose/swagger_custom.html', {
        'schema_url': '/dose/api/openapi/',
    })
# Health check view moved from views.py
from django.http import JsonResponse
from django.utils import timezone
import json
from dose.models import Tenant, UserProfile
from django.contrib.auth.models import User
def health_check(request):
    """Health check endpoint for monitoring"""
    try:
        # Basic database connectivity check
        tenant_count = Tenant.objects.count()
        user_count = User.objects.count()
        return JsonResponse({
            'status': 'healthy',
            'timestamp': json.dumps(timezone.now(), default=str),
            'database': 'connected',
            'tenants': tenant_count,
            'users': user_count
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)
# Create sample dashboard buttons view moved from views.py
from django.http import JsonResponse
from dose.models import DashboardButton
from dose.utils import get_current_tenant
@login_required
def create_sample_dashboard_buttons(request):
    """Create sample dashboard buttons for testing (Development only)"""
    current_tenant, _, err = require_tenant_membership_for_fbv(
        request, min_role=UserTenantMembership.Role.MEMBER
    )
    if err:
        return err
    # Check if user already has buttons
    existing_buttons = DashboardButton.objects.filter(
        user=request.user,
        tenant=current_tenant
    ).count()
    if existing_buttons > 0:
        return JsonResponse({
            'success': False,
            'error': f'User already has {existing_buttons} dashboard buttons'
        }, status=400)
    # Sample buttons to create
    sample_buttons = [
        {
            'title': 'Admin Panel',
            'description': 'Access the Django administration interface for system management',
            'url': '/admin/',
            'button_type': 'internal',
            'icon_style': 'emoji',
            'icon_value': '�a"!���',
            'target': '_self',
            'color': '#3498db',
            'size': 'medium',
            'sort_order': 1
        },
        {
            'title': 'Parameters',
            'description': 'Configure system parameters and application settings',
            'url': '/parameters/',
            'button_type': 'internal',
            'icon_style': 'emoji',
            'icon_value': '�x `',
            'target': '_self',
            'color': '#27ae60',
            'size': 'medium',
            'sort_order': 2
        },
        {
            'title': 'Reviews',
            'description': 'Access the reviews and feedback system',
            'url': '/reviews/',
            'button_type': 'internal',
            'icon_style': 'emoji',
            'icon_value': '���',
            'target': '_self',
            'color': '#f39c12',
            'size': 'medium',
            'sort_order': 3
        },
        {
            'title': 'API Documentation',
            'description': 'Browse API endpoints and documentation',
            'url': '/api/',
            'button_type': 'api',
            'icon_style': 'emoji',
            'icon_value': '�x R',
            'target': '_blank',
            'color': '#9b59b6',
            'size': 'large',
            'sort_order': 4
        }
    ]
    created_buttons = []
    for button_data in sample_buttons:
        button = DashboardButton.objects.create(
            user=request.user,
            tenant=current_tenant,
            **button_data
        )
        created_buttons.append({
            'id': button.id,
            'title': button.title,
            'url': button.url
        })
    return JsonResponse({
        'success': True,
        'message': f'Created {len(created_buttons)} sample dashboard buttons',
        'buttons': created_buttons
    })
# Setup demo view moved from views.py
from django.http import JsonResponse
from dose.models import Tenant, UserProfile
from django.contrib.auth.models import User
def setup_demo_view(request):
    """Setup demo data for testing the session-based tenant system"""
    messages = []
    try:
        # Create demo tenant
        demo_tenant, created = Tenant.objects.get_or_create(
            slug='demo',
            defaults={
                'name': 'Demo Company',
                'description': 'Demo tenant for testing session-based multi-tenancy',
                'tagline': 'Your Demo Environment',
                'is_active': True
            }
        )
        if created:
            messages.append(f"Created demo tenant: {demo_tenant.name}")
        else:
            messages.append(f"Demo tenant already exists: {demo_tenant.name}")
        # Create demo user
        demo_user, created = User.objects.get_or_create(
            username='demouser',
            defaults={
                'email': 'demo@example.com',
                'first_name': 'Demo',
                'last_name': 'User',
                'is_staff': True,
                'is_active': True
            }
        )
        if created:
            demo_user.set_password('demo123')
            demo_user.save()
            messages.append(f"Created demo user: {demo_user.username}")
        else:
            messages.append(f"Demo user already exists: {demo_user.username}")
        # Create user profile linking user to tenant
        user_profile, created = UserProfile.objects.get_or_create(
            user=demo_user,
            defaults={'tenant': demo_tenant}
        )
        if created:
            messages.append(f"Created user profile linking {demo_user.username} to {demo_tenant.name}")
        else:
            messages.append(f"User profile already exists for {demo_user.username}")
        # Create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            messages.append(f"Created admin user: {admin_user.username}")
        else:
            messages.append(f"Admin user already exists: {admin_user.username}")
        # Create admin profile
        admin_profile, created = UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={'tenant': demo_tenant}
        )
        if created:
            messages.append(f"Created admin profile")
        return JsonResponse({
            'success': True,
            'message': 'Demo setup completed successfully',
            'details': messages,
            'demo_credentials': {
                'username': 'demouser',
                'password': 'demo123',
                'tenant': demo_tenant.name
            },
            'admin_credentials': {
                'username': 'admin',
                'password': 'admin123',
                'tenant': demo_tenant.name
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Demo setup failed: {str(e)}',
            'details': messages
        })
# Debug view moved from views.py
from django.shortcuts import render
from dose.models import UserProfile, Tenant
from django.contrib.auth.models import User
def debug_view(request):
    """Debug view to check system status"""
    # Debug: only aggregate profiles when a real tenant is selected (never treat DB public as a tenant)
    show_profiles = False
    if request.user.is_superuser and request.session.get("tenant_slug"):
        show_profiles = True
    context = {
        'users': User.objects.all(),
        'tenants': Tenant.objects.all(),
        'user_profiles': UserProfile.objects.all() if show_profiles else [],
        'current_tenant_slug': request.session.get('tenant_slug'),
        'current_tenant_name': request.session.get('tenant_name'),
        'current_user': request.user if request.user.is_authenticated else None,
        'session_data': dict(request.session.items()),
    }
    return render(request, 'dose/debug.html', context)
# Track dashboard button click view moved from views.py
from django.http import JsonResponse
import json
from dose.utils import get_current_tenant
from dose.models import DashboardButton
def track_dashboard_button_click(request):
    """Track dashboard button clicks for analytics"""
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            current_tenant, _, err = require_tenant_membership_for_fbv(
                request, min_role=UserTenantMembership.Role.MEMBER
            )
            if err:
                return err
            data = json.loads(request.body)
            button_id = data.get('button_id')
            if button_id:
                # Get the dashboard button and verify it belongs to the current user and tenant
                try:
                    dashboard_button = DashboardButton.objects.get(
                        id=button_id,
                        user=request.user,
                        tenant=current_tenant,
                        is_active=True
                    )
                    # Track the click
                    dashboard_button.track_click()
                    return JsonResponse({
                        'success': True,
                        'clicks': dashboard_button.click_count,
                        'button_title': dashboard_button.title
                    })
                except DashboardButton.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Dashboard button not found'}, status=404)
            else:
                return JsonResponse({'success': False, 'error': 'Missing button_id'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=405)
# Track navigation click view moved from views.py
from django.http import JsonResponse
import json
from dose.utils import get_current_tenant
from dose.models import NavigationItem
def track_navigation_click(request):
    """Track navigation item clicks for analytics"""
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            current_tenant, _, err = require_tenant_membership_for_fbv(
                request, min_role=UserTenantMembership.Role.MEMBER
            )
            if err:
                return err
            data = json.loads(request.body)
            item_id = data.get('item_id')
            if item_id:
                # Get the navigation item and verify it belongs to user's tenant
                try:
                    nav_item = NavigationItem.objects.select_related('panel').get(
                        id=item_id,
                        panel__tenant=current_tenant,
                        is_active=True
                    )
                    # Check if user has permission for this item
                    if nav_item.has_permission(request.user):
                        nav_item.increment_click_count()
                        return JsonResponse({'success': True, 'clicks': nav_item.click_count})
                    else:
                        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
                except NavigationItem.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Navigation item not found'}, status=404)
            else:
                return JsonResponse({'success': False, 'error': 'Missing item_id'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=405)
# Update tenant API view moved from views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from dose.utils import get_current_tenant
@login_required
@csrf_exempt
def update_tenant_api(request):
    """API endpoint to update tenant information"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    current_tenant, _, err = require_tenant_membership_for_fbv(
        request, min_role=UserTenantMembership.Role.ADMIN
    )
    if err:
        return err
    try:
        data = json.loads(request.body)
        # Update allowed fields
        if 'name' in data:
            current_tenant.name = data['name']
            request.session['tenant_name'] = data['name']
        if 'description' in data:
            current_tenant.description = data['description']
        if 'tagline' in data:
            current_tenant.tagline = data['tagline']
        current_tenant.save()
        return JsonResponse({
            'success': True,
            'message': 'Tenant updated successfully',
            'tenant': {
                'slug': current_tenant.slug,
                'name': current_tenant.name,
                'description': current_tenant.description,
                'tagline': current_tenant.tagline
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
# Get tenant info API view moved from views.py
from django.http import JsonResponse
from dose.utils import get_current_tenant
def get_tenant_info_api(request):
    """API endpoint to get current tenant information"""
    from dose.utils import get_current_tenant_role

    current_tenant = get_current_tenant(request)
    if not current_tenant:
        return JsonResponse({'success': False, 'error': 'No tenant found for this session.'}, status=404)
    return JsonResponse({
        'success': True,
        'tenant': {
            'slug': current_tenant.slug,
            'name': current_tenant.name,
            'description': current_tenant.description,
            'logo': current_tenant.logo.url if current_tenant.logo else None,
            'tagline': current_tenant.tagline,
            'created_at': current_tenant.created_at.isoformat(),
            'is_active': current_tenant.is_active
        },
        'current_tenant_role': get_current_tenant_role(request),
    })
# Get user tenants API view moved from views.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
# Get user tenants API view moved from views.py
from django.http import JsonResponse
@login_required
def get_user_tenants_api(request):
    """API endpoint to get user's available tenants (from user_tenant_memberships)."""
    current_tenant_slug = request.session.get("tenant_slug")
    memberships = UserTenantMembership.objects.filter(user=request.user).select_related(
        "tenant"
    )
    tenants = []
    for m in memberships:
        t = m.tenant
        tenants.append(
            {
                "slug": t.slug,
                "name": t.name,
                "description": t.description,
                "logo": t.logo.url if t.logo else None,
                "role": m.role,
                "is_current": current_tenant_slug == t.slug,
            }
        )
    return JsonResponse(
        {
            "success": True,
            "tenants": tenants,
            "current_tenant_slug": current_tenant_slug,
            "current_tenant_role": request.session.get("tenant_role"),
        }
    )
# Tenant users view moved from views.py
from django.shortcuts import render
from django.contrib.auth.models import User
from dose.utils import get_current_tenant
def tenant_users(request):
    """View for managing tenant users"""
    current_tenant = get_current_tenant(request)
    if not current_tenant:
        return HttpResponseForbidden("No active tenant")
    user_ids = UserTenantMembership.objects.filter(
        tenant__slug=current_tenant.slug
    ).values_list("user_id", flat=True)
    tenant_users = User.objects.filter(id__in=user_ids)
    context = {
        'tenant': current_tenant,
        'users': tenant_users,
        'can_manage': user_can_manage_tenant_settings(request, current_tenant)
        if current_tenant
        else False
    }
    return render(request, 'dose/tenant_users.html', context)
# Tenant settings view moved from views.py
from django.shortcuts import render
import logging
from dose.utils import get_current_tenant
def tenant_settings(request):
    """View for managing tenant settings"""
    logger = logging.getLogger(__name__)
    current_tenant = get_current_tenant(request)
    logger.info(f"tenant_settings: current_tenant={current_tenant}")
    logger.info(f"tenant_settings: session keys={dict(request.session.items())}")

    can_edit = user_can_manage_tenant_settings(request, current_tenant) if current_tenant else False
    if request.method == 'POST' and can_edit:
        current_tenant.name = request.POST.get('name', current_tenant.name)
        current_tenant.description = request.POST.get('description', current_tenant.description)
        current_tenant.save()
        request.session['tenant_name'] = current_tenant.name

    # Toggle this to True to show under construction page
    show_under_construction = False
    if show_under_construction:
        return render(request, 'dose/tenant_settings_under_construction.html')
    else:
        return render(request, 'dose/tenant_settings.html', {
            'tenant': current_tenant,
            'can_edit': can_edit
        })
# Switch tenant view moved from views.py
from django.shortcuts import redirect
from dose.tenant_session import apply_tenant_to_session
def switch_tenant(request, tenant_id):
    """Allow users to switch between available tenants (membership required)."""
    if request.user.is_authenticated:
        try:
            m = UserTenantMembership.objects.select_related("tenant").get(
                user=request.user, tenant_id=tenant_id
            )
            apply_tenant_to_session(request, m.tenant, m)
            return redirect("dose:dashboard")
        except UserTenantMembership.DoesNotExist:
            return HttpResponseForbidden("You do not have access to this tenant")
    return redirect("dose:login")


@login_required
def select_tenant_view(request):
    """Post-login tenant picker when user belongs to multiple tenants."""
    memberships = (
        UserTenantMembership.objects.filter(user=request.user)
        .select_related("tenant")
        .exclude(tenant__schema_name="public")
        .order_by("tenant__name")
    )
    if request.method == "POST":
        tenant_id = request.POST.get("tenant_id")
        if tenant_id:
            try:
                m = memberships.get(tenant_id=tenant_id)
                apply_tenant_to_session(request, m.tenant, m)
                return redirect("/admin/")
            except UserTenantMembership.DoesNotExist:
                pass
    if memberships.count() == 1:
        m = memberships.first()
        apply_tenant_to_session(request, m.tenant, m)
        return redirect("/admin/")
    if memberships.count() == 0:
        return redirect("/admin/")
    return render(request, "dose/select_tenant.html", {"memberships": memberships})


# Landing page view moved from views.py
from django.shortcuts import render, redirect
from django.utils import timezone
from dose.models import UserProfile, NavigationPanel, DashboardButton, NavigationItem
from dose.utils import get_current_tenant, get_tenant_theme_colors


def _build_landing_page_context(request):
    current_tenant = get_current_tenant(request)
    user_profile = UserProfile.objects.filter(user=request.user).first() if request.user.is_authenticated else None

    if not current_tenant:
        theme_info = {
            'name': 'default',
            'display_name': 'Default'
        }
        theme_colors = get_tenant_theme_colors('tech_blue')
        status_info = {'system_status': 'operational'}
        context = {
            'current_tenant': None,
            'user_profile': user_profile,
            'theme_info': theme_info,
            'theme_colors': theme_colors,
            'status_info': status_info,
            'navigation_panels': [],
            'dashboard_buttons': [],
            'top_navigation_items': [],
            'passthrough_services': [],
            'external_services': [],
            'page_title': 'PolySaaS Industrial Strength SaaS for Limitless Horizons'
        }
        if not request.user.is_authenticated:
            login_url = f"/dose/login/?next={request.path}"
            return None, redirect(login_url)
        context['tenant_prompt'] = True
        return context, None

    theme_info = {
        'name': 'tech_blue',
        'display_name': 'Tech Blue'
    }
    theme_colors = get_tenant_theme_colors('tech_blue')
    navigation_panels = NavigationPanel.objects.filter(
        tenant=current_tenant,
        is_active=True
    ).prefetch_related('navigation_items').order_by('sort_order')

    filtered_panels = []
    for panel in navigation_panels:
        active_items = []
        for item in panel.navigation_items.filter(is_active=True).order_by('sort_order'):
            if item.has_permission(request.user):
                active_items.append(item)

        if active_items:
            panel.filtered_items = active_items
            filtered_panels.append(panel)

    from dose.models import PassThroughEndpoint, TenantApp

    try:
        _subscribed = set(
            TenantApp.public_bundles.filter(
                tenant=current_tenant,
                status__in=['active', 'provisioning'],
            ).values_list('app_name', flat=True)
        ) if current_tenant else set()
    except Exception:
        _subscribed = set()

    def _endpoint_visible(trigger_path):
        n = trigger_path.strip('/').lower().split('/')[-1].replace('-', '_')
        return n == 'gmail' or n in _subscribed

    passthrough_endpoints = [
        ep for ep in PassThroughEndpoint.objects.filter(
            is_enabled=True,
            show_in_menu=True,
        ).order_by('menu_sort_order', 'id')
        if _endpoint_visible(ep.trigger_path)
    ]

    passthrough_services = []
    external_services = []
    seen_normalized = set()
    for endpoint in passthrough_endpoints:
        norm = endpoint.trigger_path.strip('/').lower().split('/')[-1].replace('-', '_')
        if norm in seen_normalized:
            continue
        seen_normalized.add(norm)

        title = endpoint.menu_title or norm.replace('_', ' ').title()
        passthrough_services.append({
            'id': f"pt_{endpoint.id}",
            'title': title,
            'trigger': norm,
            'url': f'/pt/dose/{norm}/',
            'icon': endpoint.menu_icon or '🔗',
            'description': endpoint.description or f"Access {title}"
        })

    dashboard_buttons = DashboardButton.objects.filter(
        user=request.user,
        tenant=current_tenant,
        is_active=True
    ).order_by('sort_order')

    status_info = {
        'system_status': 'operational',
        'last_login': request.user.last_login,
        'tenant_users_count': UserProfile.objects.filter(tenant=current_tenant).count() if current_tenant else 0,
        'current_time': timezone.now(),
        'total_navigation_panels': len(filtered_panels),
        'total_navigation_items': sum(len(panel.filtered_items) for panel in filtered_panels),
        'dashboard_buttons_count': dashboard_buttons.count()
    }

    top_navigation_items = [
        {'name': 'Dashboard', 'url': '/dose/dashboard/', 'icon': '📊'},
        {'name': 'About', 'url': '/dose/about/', 'icon': 'ℹ️'},
        {'name': 'Admin Panel', 'url': '/admin/', 'icon': '⚙️'},
        {'name': 'DoseAI Prompt & History', 'url': '/dose/doseai/', 'icon': '🤖'},
        {'name': 'Switch Tenant', 'url': '/dose/switch-tenant/', 'icon': '🔄'},
        {'name': 'Logout', 'url': '/dose/logout/', 'icon': '🚪'}
    ]

    if current_tenant:
        try:
            passthrough_panel = NavigationPanel.objects.filter(
                tenant=current_tenant,
                title__iexact='External Services',
                is_active=True
            ).prefetch_related('navigation_items').first()
            if passthrough_panel:
                passthrough_items = passthrough_panel.navigation_items.filter(is_active=True).order_by('sort_order')
                for item in passthrough_items:
                    if item.has_permission(request.user):
                        top_navigation_items.append({
                            'name': item.title,
                            'url': item.url,
                            'icon': item.icon_value or '🔗',
                        })
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error loading passthrough navigation items: {e}")

    context = {
        'current_tenant': current_tenant,
        'tenant_name': current_tenant.name if current_tenant else '',
        'user_profile': user_profile,
        'theme_info': theme_info,
        'theme_colors': theme_colors,
        'status_info': status_info,
        'passthrough_endpoints': passthrough_endpoints,
        'passthrough_services': passthrough_services,
        'external_services': external_services,
        'navigation_panels': filtered_panels,
        'dashboard_buttons': dashboard_buttons,
        'top_navigation_items': top_navigation_items,
        'page_title': 'PolySaaS Industrial Strength SaaS for Limitless Horizons'
    }
    return context, None


def _resolve_landing_passthrough_endpoint(trigger):
    from dose.models import PassThroughEndpoint

    endpoint = PassThroughEndpoint.objects.filter(
        trigger_path__iexact=trigger,
        is_enabled=True,
    ).order_by('-id').first()
    if endpoint is None and '_' in trigger:
        endpoint = PassThroughEndpoint.objects.filter(
            trigger_path__iexact=trigger.replace('_', ''),
            is_enabled=True,
        ).order_by('-id').first()
    if endpoint is None:
        for candidate in PassThroughEndpoint.objects.filter(is_enabled=True).order_by('-id'):
            norm = candidate.trigger_path.strip('/').lower().split('/')[-1].replace('-', '_')
            if norm == trigger:
                return candidate
    return endpoint


def _retarget_passthrough_prefixes_for_dose(html, trigger):
    if not html:
        return html
    admin_prefix = f'/pt/admin/{trigger}'
    dose_prefix = f'/pt/dose/{trigger}'
    try:
        profile = UserProfile.objects.get(user=user)
        profile_info = {
            'user_id': profile.user.id,
            'tenant_slug': profile.tenant.slug,
            'tenant_name': profile.tenant.name,
        }
        tenant_info = {
            'slug': profile.tenant.slug,
            'name': profile.tenant.name,
            'is_active': profile.tenant.is_active,
        }
    except UserProfile.DoesNotExist:
        profile_info = 'No UserProfile found'
    return JsonResponse({
        'user': user.username,
        'session_keys': session_keys,
        'profile_info': profile_info,
        'tenant_info': tenant_info,
    })
@login_required
def pt_dose_generic_passthrough_view(request, trigger, subpath=None):
    from dose.admin_views import _process_upstream_html_for_embed, _split_html_document_for_jazzmin_embed
    from dose.models import UserTenantMembership
    from dose.passthrough.forwarding import fetch_upstream_index_html
    from dose.passthrough.handlers.registry import get_handler_for_endpoint
    from dose.utils import get_current_tenant

    context, response = _build_landing_page_context(request)
    if response is not None:
        return response

    tenant = get_current_tenant(request)
    if not tenant:
        return HttpResponseForbidden('Tenant context is required for passthrough.')
    if not request.user.is_superuser and not UserTenantMembership.objects.filter(
        user=request.user, tenant=tenant
    ).exists():
        return HttpResponseForbidden('You do not have access to this tenant.')

    norm = trigger.strip('/').lower().split('/')[-1].replace('-', '_')
    allowed_triggers = {service.get('trigger') for service in context.get('passthrough_services', [])}
    if norm not in allowed_triggers:
        raise Http404('Not found')

    endpoint = _resolve_landing_passthrough_endpoint(norm)
    if endpoint is None:
        raise Http404('No enabled PassThroughEndpoint matches this URL.')

    handler = get_handler_for_endpoint(endpoint, request)
    upstream_subpath = '/'
    if subpath:
        upstream_subpath = '/' + subpath.lstrip('/')

    raw_html = fetch_upstream_index_html(
        request,
        endpoint.endpoint_url,
        upstream_subpath=upstream_subpath,
        handler=handler,
    )

    embed_title = endpoint.menu_title or norm.replace('_', ' ').title()
    embed_head = ''
    embed_body = ''
    if raw_html and raw_html.startswith('REDIRECT:'):
        parts = raw_html.split(':', 2)
        status_code = int(parts[1]) if len(parts) > 1 else 302
        location = parts[2] if len(parts) > 2 else '/'
        embed_body = mark_safe(
            '<div class="landing-passthrough-message error">'
            f'Upstream returned {status_code} redirect to <code>{location}</code>.'
            '</div>'
        )
    elif raw_html:
        processed = _process_upstream_html_for_embed(handler, raw_html, request, endpoint.endpoint_url)
        processed = _retarget_passthrough_prefixes_for_dose(processed, norm)
        head_inner, body_html = _split_html_document_for_jazzmin_embed(processed)
        embed_head = mark_safe(head_inner)
        embed_body = mark_safe(
            f'<div class="polysaas-passthrough-scope" data-polysaas-embed-trigger="{norm}">{body_html or ""}</div>'
        )
    else:
        embed_body = mark_safe(
            '<div class="landing-passthrough-message error">'
            'Could not load upstream HTML. Check the endpoint URL and upstream service.'
            '</div>'
        )

    context.update({
        'page_title': 'PolySaaS Industrial Strength SaaS for Limitless Horizons',
        'passthrough_embed_head': embed_head,
        'passthrough_embed_body': embed_body,
        'passthrough_embed_title': embed_title,
        'passthrough_embed_trigger': norm,
        'passthrough_embed_path': request.path_info,
    })
    return render(request, 'dose/landing_page.html', context)
# Dashboard view moved from views.py
from django.shortcuts import render
def dashboard(request):
    """Basic dashboard view for Django."""
    from dose.models import Tenant, UserProfile, ErrorLog
    from django.utils import timezone
    from datetime import timedelta

    # Get current tenant
    tenant = None
    try:
        profile = UserProfile.objects.get(user=request.user)
        tenant = profile.tenant
    except (UserProfile.DoesNotExist, AttributeError):
        tenant_slug = request.session.get('tenant_slug') or request.session.get('tenant_id')
        if tenant_slug:
            try:
                tenant = Tenant.objects.get(slug=tenant_slug)
            except Tenant.DoesNotExist:
                pass

    # Get active users count (dummy data for now)
    active_users = 5

    # Get requests in last hour (dummy data for now)
    requests_last_hour = 42

    # Get recent errors
    tenant_errors = []
    if tenant:
        one_hour_ago = timezone.now() - timedelta(hours=1)
        tenant_errors = ErrorLog.objects.filter(
            tenant=tenant,
            timestamp__gte=one_hour_ago
        ).order_by('-timestamp')[:5]

    context = {
        'tenant': tenant,
        'active_users': active_users,
        'requests_last_hour': requests_last_hour,
        'tenant_errors': tenant_errors,
    }

    return render(request, 'dose/dashboard.html', context)
# Logout view
from django.contrib.auth import logout

def logout_view(request):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"logout_view: Logging out user {getattr(request.user, 'username', None)}. Session keys before logout: {list(request.session.keys())}")
    logout(request)
    logger.info(f"logout_view: Session keys after logout: {list(request.session.keys())}")
    return redirect('/')
# Login view
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
import logging
from dose.models import UserProfile
from dose.tenant_session import apply_tenant_to_session

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            logger = logging.getLogger(__name__)
            try:
                # Ensure UserProfile and UserTenantMembership exist for this user/tenant
                try:
                    profile = UserProfile.objects.get(user=user)
                except UserProfile.DoesNotExist:
                    # Fallback: assign to first tenant or create a default tenant
                    tenant = Tenant.objects.first()
                    if not tenant:
                        tenant = Tenant.objects.create(name="Default Tenant", slug="default-tenant", schema_name="public")
                    profile = UserProfile.objects.create(user=user, tenant=tenant)
                tenant = profile.tenant
                # Always ensure UserTenantMembership exists
                m, _ = UserTenantMembership.objects.get_or_create(
                    user=user,
                    tenant=tenant,
                    defaults={"role": UserTenantMembership.Role.MEMBER},
                )
                from django.db import connection
                schema_name = tenant.slug if hasattr(tenant, 'slug') else tenant.schema_name
                with connection.cursor() as cursor:
                    cursor.execute(f'SET search_path TO "{schema_name}",public;')
                apply_tenant_to_session(request, tenant, m)
                logger.info(
                    f"login_view: Set tenant session keys for user {user.username}: tenant_slug={tenant.slug}, tenant_name={tenant.name}"
                )
                logger.info(f"login_view: Session keys after set: {list(request.session.keys())}")
            except Exception as e:
                logger.warning(f"login_view: Exception in tenant session setup for user {user.username}: {e}")
            next_url = request.GET.get('next') or '/'
            return redirect(next_url)
        else:
            return render(request, 'dose/login.html', {'error': 'Invalid username or password'})
    return render(request, 'dose/login.html')
# Debug tenant session view
def debug_tenant_session(request):
    from dose.models import UserProfile, Tenant
    user = request.user
    session_keys = dict(request.session.items())
    profile_info = None
    tenant_info = None
    try:
        profile = UserProfile.objects.get(user=user)
        profile_info = {
            'user_id': profile.user.id,
            'tenant_slug': profile.tenant.slug,
            'tenant_name': profile.tenant.name,
        }
        tenant_info = {
            'slug': profile.tenant.slug,
            'name': profile.tenant.name,
            'is_active': profile.tenant.is_active,
        }
    except UserProfile.DoesNotExist:
        profile_info = 'No UserProfile found'
    return JsonResponse({
        'user': user.username,
        'session_keys': session_keys,
        'profile_info': profile_info,
        'tenant_info': tenant_info,
    })

# AtomicServiceViewSet
from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.contrib import messages as django_messages
from dose.models import AtomicService
from dose.serializers import AtomicServiceSerializer

class AtomicServiceViewSet(viewsets.ModelViewSet):
    queryset = AtomicService.objects.all()
    serializer_class = AtomicServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def _get_messages_list(self, request):
        """Extract Django messages and return as list of dicts."""
        messages_list = []
        if hasattr(request, '_messages'):
            for message in django_messages.get_messages(request):
                messages_list.append({
                    'text': str(message),
                    'level': message.level_tag,
                    'tags': message.tags
                })
        return messages_list

    def _add_messages_to_response(self, response_data, request):
        """Add Django messages to the response data."""
        messages_list = self._get_messages_list(request)
        if messages_list:
            response_data['_messages'] = messages_list
        return response_data

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data = self._add_messages_to_response(response.data, request)
        return response

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        response.data = self._add_messages_to_response(response.data, request)
        return response

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data = self._add_messages_to_response(response.data, request)
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = self._add_messages_to_response(response.data, request)
        return response

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        response.data = self._add_messages_to_response(response.data, request)
        return response

    def perform_create(self, serializer):
        instance = serializer.save()
        return instance

# RequestLogViewSet
from dose.models import RequestLog, ErrorLog, Subscription
from dose.serializers import RequestLogSerializer, ErrorLogSerializer, SubscriptionSerializer

class RequestLogViewSet(viewsets.ModelViewSet):
    queryset = RequestLog.objects.all()
    serializer_class = RequestLogSerializer
    permission_classes = [permissions.IsAdminUser]

class ErrorLogViewSet(viewsets.ModelViewSet):
    queryset = ErrorLog.objects.all()
    serializer_class = ErrorLogSerializer
    permission_classes = [permissions.IsAdminUser]

# GitHub profile passthrough view
from allauth.socialaccount.models import SocialToken
import requests

def github_api_passthrough(user, api_path):
    try:
        token = SocialToken.objects.get(account__user=user, account__provider='github')
        access_token = token.token
    except SocialToken.DoesNotExist:
        return None
    url = f'https://api.github.com{api_path}'
    headers = {
        'Authorization': f'token {access_token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    response = requests.get(url, headers=headers)
    return response

from django.http import JsonResponse

def github_profile_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    response = github_api_passthrough(request.user, '/user')
    if response and response.status_code == 200:
        return JsonResponse(response.json())
    return JsonResponse({'error': 'Unable to fetch profile'}, status=400)
# Google and Facebook profile passthrough views
from django.http import JsonResponse

def get_social_token(user, provider):
    from allauth.socialaccount.models import SocialToken
    try:
        token = SocialToken.objects.get(account__user=user, account__provider=provider)
        return token.token
    except SocialToken.DoesNotExist:
        return None

def google_api_passthrough(user, api_path):
    import requests
    access_token = get_social_token(user, 'google')
    if not access_token:
        return None
    url = f'https://www.googleapis.com{api_path}'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    }
    response = requests.get(url, headers=headers)
    return response

def facebook_api_passthrough(user, api_path):
    import requests
    access_token = get_social_token(user, 'facebook')
    if not access_token:
        return None
    url = f'https://graph.facebook.com{api_path}'
    params = {
        'access_token': access_token,
    }
    response = requests.get(url, params=params)
    return response

def google_profile_view(request):
    import logging
    logger = logging.getLogger(__name__)
    if not request.user.is_authenticated:
        logger.info("google_profile_view: Not authenticated user attempted access.")
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    response = google_api_passthrough(request.user, '/oauth2/v2/userinfo')
    if response and response.status_code == 200:
        profile = response.json()
        uid = profile.get('id')
        email = profile.get('email')
        logger.info(f"google_profile_view: User {request.user.username} Google UID: {uid}, email: {email}")
        return JsonResponse(profile)
    logger.warning(f"google_profile_view: Unable to fetch profile for user {request.user.username}")
    return JsonResponse({'error': 'Unable to fetch profile'}, status=400)

def facebook_profile_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    response = facebook_api_passthrough(request.user, '/me?fields=id,name,email')
    if response and response.status_code == 200:
        return JsonResponse(response.json())
    return JsonResponse({'error': 'Unable to fetch profile'}, status=400)
# Passthrough views
def passthrough_iframe_view(request):
    provider = request.GET.get('provider', 'custom')
    from dose.models import PassThroughEndpoint
    endpoint = PassThroughEndpoint.objects.filter(provider=provider).first()
    passthrough_url = endpoint.endpoint_url if endpoint else 'https://github.com'
    return render(request, 'passthrough_iframe.html', {'passthrough_url': passthrough_url})

def passthrough_html_view(request):
    import requests
    provider = request.GET.get('provider', 'custom')
    from dose.models import PassThroughEndpoint
    endpoint = PassThroughEndpoint.objects.filter(provider=provider).first()
    passthrough_url = endpoint.endpoint_url if endpoint else 'https://github.com'
    html_content = ''
    try:
        response = requests.get(passthrough_url)
        html_content = response.text
    except Exception as e:
        html_content = f'<div class="error">Error fetching content: {e}</div>'
    return render(request, 'passthrough_html.html', {'html_content': html_content})
# Main views for Dose
from django.shortcuts import render
from django.conf import settings

def subscribe_view(request):
    import json
    from django.contrib.auth import logout

    plan_prices = getattr(settings, 'PLAN_PRICES', {})
    plan_max_apps = getattr(settings, 'PLAN_MAX_APPS', {})
    plan_context = {
        'SUBSCRIPTION_AMOUNT': plan_prices.get('polysaas-1', 26.00),
        'STRIPE_PUBLISHABLE_KEY': getattr(settings, 'STRIPE_PUBLISHABLE_KEY', ''),
        'PRICE_1': plan_prices.get('polysaas-1', 26.00),
        'PRICE_3': plan_prices.get('polysaas-3', 49.00),
        'PRICE_UNLIMITED': plan_prices.get('polysaas-unlimited', 99.00),
        # Prefer dicts + |json_script in template (escapejs on JSON breaks JSON.parse).
        'plan_prices': plan_prices,
        'plan_max_apps': plan_max_apps,
        'PLAN_PRICES_JSON': json.dumps(plan_prices),
        'PLAN_MAX_APPS_JSON': json.dumps(plan_max_apps),
        # Public marketing signup only — session cleared on each GET (see below).
        'subscribe_new_tenant_flow': True,
    }
    if request.method == 'POST':
        return render(request, 'dose/connect_social.html', plan_context)
    # Strip any in-app login / tenant session so subscribe is always an outside, anonymous flow.
    logout(request)
    request.session.flush()
    return render(request, 'dose/subscribe.html', plan_context)

# ...other views from dose/views.py will be moved here...
