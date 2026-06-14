#!/usr/bin/env python
"""
Quick setup script for Orchestration Dashboard Demo
Creates sample instructions and ensures atomic services are registered
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import Instruction, AtomicService, Tenant
from dose.services.atomic_services_registry import init_atomic_services_registry, ATOMIC_SERVICE_REGISTRY
from django.contrib.auth.models import User

def setup_orchestration_demo():
    """Setup everything needed for the orchestration demo"""
    
    print("=" * 80)
    print("ORCHESTRATION DASHBOARD DEMO SETUP")
    print("=" * 80)
    
    # Step 1: Initialize atomic services registry
    print("\n1. Initializing Atomic Services Registry...")
    init_atomic_services_registry()
    print(f"   ✅ Found {len(ATOMIC_SERVICE_REGISTRY)} atomic services:")
    for service_name in ATOMIC_SERVICE_REGISTRY.keys():
        print(f"      - {service_name}")
    
    # Step 2: Ensure AtomicService records exist
    print("\n2. Ensuring AtomicService database records...")
    from populate_atomic_services import populate_atomic_services
    populate_atomic_services()
    
    # Step 3: Get or create demo tenant
    print("\n3. Setting up demo tenant...")
    try:
        tenant = Tenant.objects.filter(name__icontains='oliver').first()
        if not tenant:
            tenant = Tenant.objects.first()
        if tenant:
            print(f"   ✅ Using tenant: {tenant.name}")
        else:
            print("   ⚠️  No tenant found - create one first")
            return
    except Exception as e:
        print(f"   ❌ Error getting tenant: {e}")
        return
    
    # Step 4: Create sample instructions if they don't exist
    print("\n4. Creating sample instructions for demo...")
    
    sample_instructions = [
        {
            'requestpath': '/api/users/create',
            'requestmethod': 'POST',
            'executescript': 'AtomicService1',
            'description': 'User creation endpoint - triggers AtomicService1 to log and notify',
            'direction': 'REQ',
            'save_callbackdata': True,
        },
        {
            'requestpath': '/api/tickets/new',
            'requestmethod': 'POST',
            'executescript': 'TicketInterceptorService',
            'description': 'Ticket creation - intercepts and forwards to external service',
            'direction': 'REQ',
            'save_callbackdata': True,
        },
        {
            'requestpath': '/api/copilot/query',
            'requestmethod': 'POST',
            'executescript': 'CopilotQuery',
            'description': 'AI query endpoint - processes with Copilot service',
            'direction': 'REQ',
            'save_callbackdata': True,
        },
        {
            'requestpath': '/admin/dashboard/',
            'requestmethod': 'GET',
            'executescript': 'AtomicService1',
            'description': 'Dashboard page load - triggers welcome message service',
            'direction': 'REQ',
            'save_callbackdata': False,
        },
    ]
    
    created_count = 0
    existing_count = 0
    
    for instr_data in sample_instructions:
        existing = Instruction.objects.filter(
            tenant=tenant,
            requestpath=instr_data['requestpath'],
            requestmethod=instr_data['requestmethod']
        ).first()
        
        if not existing:
            try:
                Instruction.objects.create(tenant=tenant, **instr_data)
                print(f"   ✅ Created: {instr_data['requestmethod']} {instr_data['requestpath']} → {instr_data['executescript']}")
                created_count += 1
            except Exception as e:
                print(f"   ❌ Error creating {instr_data['requestpath']}: {e}")
        else:
            print(f"   ⏭️  Exists: {instr_data['requestmethod']} {instr_data['requestpath']}")
            existing_count += 1
    
    print(f"\n   📊 Summary: {created_count} created, {existing_count} already existed")
    
    # Step 5: Show access instructions
    print("\n" + "=" * 80)
    print("✅ SETUP COMPLETE!")
    print("=" * 80)
    print("\n🚀 Access your Orchestration Dashboard at:")
    print("   http://localhost:8000/dose/orchestration/")
    print("\n📋 What you can demo:")
    print("   1. View all instructions and their matched atomic services")
    print("   2. Click on an instruction to see which service it triggers")
    print("   3. Click 'New Instruction' to create one dynamically")
    print("   4. See the orchestration flow visualization")
    print("   5. View recent execution logs")
    print("\n💡 For admin access:")
    print("   http://localhost:8000/admin/")
    print("   Look for the 'Launch Dashboard' button at the top!")
    print("\n" + "=" * 80)

if __name__ == '__main__':
    setup_orchestration_demo()
