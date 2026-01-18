@login_required
def create_sample_dashboard_buttons(request):
    """Create sample dashboard buttons for testing (Development only)"""
    current_tenant = get_current_tenant(request)
    
    if not current_tenant:
        return JsonResponse({'success': False, 'error': 'No active tenant'}, status=400)
    
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
            'icon_value': '⚙️',
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
            'icon_value': '📊',
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
            'icon_value': '⭐',
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
            'icon_value': '🔌',
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
