from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
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
