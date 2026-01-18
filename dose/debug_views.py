from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from dose.models import Tenant

def list_tenants_api(request):
    """Simple API to list all tenants for debugging"""
    try:
        tenants = Tenant.objects.all()
        tenant_data = []
        
        for tenant in tenants:
            tenant_data.append({
                'name': tenant.name,
                'schema_name': tenant.schema_name,
                'tagline': tenant.tagline,
                'created_on': tenant.created_on.isoformat() if tenant.created_on else None,
            })
        
        return JsonResponse({
            'count': len(tenant_data),
            'tenants': tenant_data
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'count': 0,
            'tenants': []
        })

def tenant_admin_test(request):
    """Test view that mimics admin behavior"""
    try:
        tenants = Tenant.objects.all()
        
        html = "<html><head><title>Tenant Admin Test</title></head><body>"
        html += "<h1>Tenant Admin Test</h1>"
        html += f"<p>Found {tenants.count()} tenants:</p>"
        html += "<table border='1'><tr><th>Name</th><th>Schema</th><th>Tagline</th><th>Created</th></tr>"
        
        for tenant in tenants:
            html += f"<tr><td>{tenant.name}</td><td>{tenant.schema_name}</td><td>{tenant.tagline or 'N/A'}</td><td>{tenant.created_on}</td></tr>"
        
        html += "</table>"
        html += "<p><a href='/admin/dose/tenant/'>Go to Real Admin</a></p>"
        html += "</body></html>"
        
        return HttpResponse(html)
        
    except Exception as e:
        return HttpResponse(f"Error: {e}")
