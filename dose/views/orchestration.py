from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from dose.models import Instruction, AtomicService
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
                'executescript': 'EndpointDataExtractorService',
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


@login_required
def get_orchestration_instruction(request, action_path):
    """GB-ORCH-EDIT-004: Return existing instruction for update or new for create"""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        try:
            from dose.utils import get_current_tenant
            tenant = get_current_tenant(request)
        except Exception:
            tenant = None

    if not tenant:
        return JsonResponse({'status': 'no_tenant'})

    instruction = Instruction.objects.filter(
        tenant=tenant,
        requestpath=action_path
    ).first()

    if instruction:
        # Update mode
        return JsonResponse({
            'status': 'success',
            'mode': 'update',
            'id': instruction.id,
            'action_path': instruction.requestpath,
            'instruction_text': instruction.description or '',
            'executescript': instruction.executescript or '',
            'direction': instruction.direction or 'REQ',
        })
    else:
        # Create mode
        return JsonResponse({
            'status': 'success',
            'mode': 'create',
            'action_path': action_path,
            'instruction_text': '',
            'executescript': '',
            'direction': 'REQ',
        })
