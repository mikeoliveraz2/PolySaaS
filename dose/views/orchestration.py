# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Orchestration Bar + Instruction Embed — commit 8cd810c0
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.urls import reverse
from urllib.parse import quote
from dose.models import Instruction, AtomicService
from dose.passthrough.orchestration_hook import find_matching_instructions
from dose.models.request_log import RequestLog
from dose.services.atomic_services_registry import init_atomic_services_registry, ATOMIC_SERVICE_REGISTRY

@login_required
def orchestration_dashboard(request):
    """
    Main orchestration dashboard showing instructions, atomic services, and dynamic matching
    """
    # Initialize services registry
    init_atomic_services_registry()
    
    # Get tenant context
    tenant = getattr(request, 'tenant', None)
    
    # Get all instructions for this tenant
    if tenant:
        instructions = Instruction.objects.filter(tenant=tenant).order_by('-pub_date')
    else:
        instructions = Instruction.objects.all().order_by('-pub_date')
    
    # Get all atomic services from database
    atomic_services = AtomicService.objects.all().order_by('service_name')
    
    # Get execution stats
    today = timezone.now().date()
    executions_today = RequestLog.objects.filter(
        timestamp__date=today,
        body__icontains='instruction'
    ).count()
    
    # Get recent execution logs
    recent_logs = RequestLog.objects.filter(
        body__icontains='instruction'
    ).order_by('-timestamp')[:10]
    
    context = {
        'tenant': tenant,
        'instructions': instructions,
        'instructions_count': instructions.count(),
        'atomic_services': atomic_services,
        'services_count': atomic_services.count(),
        'executions_today': executions_today,
        'recent_logs': recent_logs,
        'registry_services': ATOMIC_SERVICE_REGISTRY,
    }
    
    return render(request, 'dose/orchestration_dashboard.html', context)


@login_required
def create_instruction(request):
    """
    Create a new instruction from the dashboard
    """
    if request.method == 'POST':
        try:
            tenant = getattr(request, 'tenant', None)
            
            # Create the instruction
            instruction = Instruction.objects.create(
                tenant=tenant,
                requestpath=request.POST.get('requestpath'),
                requestmethod=request.POST.get('requestmethod', 'GET'),
                executescript=request.POST.get('executescript'),
                direction=request.POST.get('direction', 'REQ'),
                description=request.POST.get('description', 'New instruction'),
                eventKey=request.POST.get('eventKey', ''),
                save_callbackdata=request.POST.get('save_callbackdata') == 'true'
            )
            
            messages.success(request, f'Instruction created successfully! Path: {instruction.requestpath}')
            
            # Try to execute the atomic service if available
            if instruction.executescript:
                from dose.services.atomic_services_registry import get_atomic_service
                service_class = get_atomic_service(instruction.executescript)
                if service_class:
                    try:
                        service_class.execute_and_save(request, instruction)
                        messages.info(request, f'Atomic service "{instruction.executescript}" executed successfully!')
                    except Exception as e:
                        messages.warning(request, f'Instruction created but service execution failed: {str(e)}')
        
        except Exception as e:
            messages.error(request, f'Error creating instruction: {str(e)}')
    
    return redirect('dose:orchestration_dashboard')


@login_required
def demo_view_invoices(request):
    """
    Demo: simulate 'View Invoices' orchestration trigger.
    Creates an instruction for GET /web/dataset/call_kw/account.move if it doesn't exist,
    and shows a green toast confirming the orchestration flow.
    """
    tenant = getattr(request, 'tenant', None)

    try:
        from django.db import connection
        # Ensure tenant schema context
        if tenant and tenant.schema_name:
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO "{tenant.schema_name}",public;')

        # Create or get the invoice-view instruction
        instruction, created = Instruction.objects.get_or_create(
            tenant=tenant,
            requestpath='/web/dataset/call_kw/account.move',
            requestmethod='POST',
            defaults={
                'eventKey': 'polysaas.odoo.invoice.viewed',
                'description': 'Demo: Odoo View Invoices orchestration',
                'direction': 'REQ',
                'executescript': 'EndpointDataExtractor',
                'appusername': 'demo',
                'save_callbackdata': True,
            },
        )

        # Log the demo action
        RequestLog.objects.create(
            method='DEMO',
            path='/orchestration/demo/view-invoices/',
            body={'instruction_id': instruction.pk, 'event': 'demo_view_invoices'},
            tenant=tenant,
        )

        messages.success(
            request,
            f'✅ View Invoices orchestration triggered! Instruction {"created" if created else "reused"} (ID: {instruction.pk}). '
            f'Odoo invoice data will be captured and published to topic: {instruction.eventKey}'
        )

    except Exception as e:
        messages.error(request, f'View Invoices demo failed: {str(e)}')

    return redirect('dose:orchestration_dashboard')


def _normalize_action_path(action_path):
    path = (action_path or '').strip()
    if not path:
        return '/'
    if not path.startswith('/'):
        path = '/' + path
    return path


def _resolve_active_bootswatch_theme(request):
    """Resolve active Bootswatch theme + light/dark mode (same rules as jazzmin_theme CP)."""
    allowed = {
        'default', 'cerulean', 'cosmo', 'cyborg', 'darkly', 'flatly', 'journal', 'litera',
        'lumen', 'lux', 'materia', 'minty', 'pulse', 'sandstone', 'simplex', 'sketchy',
        'slate', 'solar', 'spacelab', 'superhero', 'united', 'yeti',
    }
    light_theme = 'flatly'
    dark_theme = 'darkly'
    if getattr(request, 'user', None) and request.user.is_authenticated:
        try:
            from dose.models import UserProfile
            from dose.utils import get_current_tenant
            tenant = get_current_tenant(request)
            if tenant:
                profile = UserProfile.objects.filter(user=request.user, tenant=tenant).first()
                if profile:
                    light_theme = profile.light_theme or light_theme
                    dark_theme = profile.dark_theme or dark_theme
        except Exception:
            pass
    display_mode = request.session.get('display_mode', 'light')
    if request.COOKIES.get('display_mode'):
        display_mode = request.COOKIES.get('display_mode')
    display_mode = (display_mode or 'light').lower()
    theme = light_theme if display_mode == 'light' else (dark_theme or 'darkly')
    if theme not in allowed:
        theme = 'flatly' if display_mode == 'light' else 'darkly'
    return theme, display_mode


def _embed_theme_query(request):
    theme, mode = _resolve_active_bootswatch_theme(request)
    return '&orch_theme=' + quote(theme, safe='') + '&orch_mode=' + quote(mode, safe='')


def _instruction_admin_url(instruction):
    return reverse('admin:dose_instruction_change', args=[instruction.pk])


def _instruction_embed_add_url(action_path, method='GET', request=None):
    qs = (
        'requestpath=' + quote(action_path, safe='')
        + '&match_type=path'
        + '&direction=REQ'
        + '&requestmethod=' + quote(method.upper(), safe='')
        + '&_popup=1'
    )
    url = reverse('dose:orchestration_instruction_embed_add') + '?' + qs
    if request is not None:
        url += _embed_theme_query(request)
    return url


def _instruction_embed_change_url(instruction, request=None):
    url = reverse('dose:orchestration_instruction_embed_change', args=[instruction.pk]) + '?_popup=1'
    if request is not None:
        url += _embed_theme_query(request)
    return url


def _instruction_add_url(action_path, method='GET'):
    qs = (
        'requestpath=' + quote(action_path, safe='')
        + '&match_type=path'
        + '&direction=REQ'
        + '&requestmethod=' + quote(method.upper(), safe='')
    )
    return reverse('admin:dose_instruction_add') + '?' + qs


@login_required
def get_orchestration_instruction(request, action_path):
    """GB-ORCH-EDIT-004/005: Match instruction (orchestration rules) and return admin form URL."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        try:
            from dose.utils import get_current_tenant
            tenant = get_current_tenant(request)
        except Exception:
            tenant = None

    if not tenant:
        return JsonResponse({'status': 'no_tenant'})

    normalized_path = _normalize_action_path(action_path)
    method = (request.GET.get('method') or 'GET').upper()
    matched = find_matching_instructions(tenant, normalized_path, method=method, direction='REQ')
    instruction = matched[0] if matched else None

    if instruction:
        return JsonResponse({
            'status': 'success',
            'mode': 'update',
            'id': instruction.id,
            'action_path': instruction.requestpath or normalized_path,
            'instruction_text': instruction.description or '',
            'executescript': instruction.executescript or '',
            'direction': instruction.direction or 'REQ',
            'admin_url': _instruction_embed_change_url(instruction, request),
            'full_admin_url': _instruction_admin_url(instruction),
            'match_count': len(matched),
        })

    return JsonResponse({
        'status': 'success',
        'mode': 'create',
        'action_path': normalized_path,
        'instruction_text': '',
        'executescript': '',
        'direction': 'REQ',
        'admin_url': _instruction_embed_add_url(normalized_path, method=method, request=request),
        'full_admin_url': _instruction_add_url(normalized_path, method=method),
        'match_count': 0,
    })
