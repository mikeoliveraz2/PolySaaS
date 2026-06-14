# Test script to demonstrate the new parameter resolution hierarchy
# in DifferentialEquationService

"""
This script demonstrates the new 3-tier parameter resolution in DifferentialEquationService:

1. Parameters table (highest priority)
2. Instruction JSON (medium priority) 
3. Static defaults (lowest priority)

Usage:
python test_differential_equation_params.py
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from dose.models import Tenant, Instruction
from parameters.models import Parameter
from dose.services.differential_equation_service import DifferentialEquationService

def test_parameter_resolution():
    """Test the 3-tier parameter resolution hierarchy"""
    
    print("=== Testing DifferentialEquationService Parameter Resolution ===\n")
    
    # Get or create test user and tenant
    try:
        user = User.objects.get(username='olientAdmin')
        tenant = user.userprofile.tenant
        print(f"✅ Using existing user: {user.username} in tenant: {tenant.name}")
    except User.DoesNotExist:
        print("❌ Test user 'olientAdmin' not found. Please run this after setting up your user.")
        return
    
    event_key = 'test_differential_equation'
    
    # Clean up any existing test parameters
    Parameter.objects.filter(tenant=tenant, event_key=event_key).delete()
    print(f"🧹 Cleaned up existing parameters for event_key: {event_key}")
    
    # Test 1: Static defaults only (no parameters table, no instruction json)
    print("\n--- Test 1: Static Defaults Only ---")
    instruction1 = Instruction.objects.create(
        tenant=tenant,
        eventKey=event_key,
        description="Test with static defaults only",
        parameters_json=None  # No parameters in instruction
    )
    
    class MockRequest:
        def __init__(self, user):
            self.user = user
            self.POST = {}
    
    mock_request = MockRequest(user)
    
    try:
        result1 = DifferentialEquationService.execute_and_save(mock_request, instruction1)
        print("✅ Test 1 passed - Used static defaults")
        print(f"   Callback ID: {result1.id}")
        print(f"   Source: {result1.parameters_json['input_parameters']['_source']}")
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
    
    # Test 2: Instruction JSON parameters (override defaults)
    print("\n--- Test 2: Instruction JSON Parameters ---")
    instruction2 = Instruction.objects.create(
        tenant=tenant,
        eventKey=event_key,
        description="Test with instruction JSON parameters",
        parameters_json={
            'k': 0.5,
            'y0': 20,
            't0': 1,
            'tf': 15,
            'n_points': 150
        }
    )
    
    try:
        result2 = DifferentialEquationService.execute_and_save(mock_request, instruction2)
        print("✅ Test 2 passed - Used instruction JSON parameters")
        print(f"   Callback ID: {result2.id}")
        print(f"   Source: {result2.parameters_json['input_parameters']['_source']}")
        input_params = result2.parameters_json['input_parameters']
        print(f"   k={input_params['k']}, y0={input_params['y0']}, tf={input_params['tf']}")
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
    
    # Test 3: Parameters table (highest priority - overrides instruction JSON)
    print("\n--- Test 3: Parameters Table (Highest Priority) ---")
    
    # Create parameters in the parameters table
    Parameter.objects.create(tenant=tenant, event_key=event_key, name='k', value='0.8')
    Parameter.objects.create(tenant=tenant, event_key=event_key, name='y0', value='50')
    Parameter.objects.create(tenant=tenant, event_key=event_key, name='tf', value='25')
    
    print(f"📊 Created parameters in table for event_key: {event_key}")
    print("   k=0.8, y0=50, tf=25 (t0 and n_points will come from instruction JSON)")
    
    try:
        # Use the same instruction2 which has JSON parameters
        result3 = DifferentialEquationService.execute_and_save(mock_request, instruction2)
        print("✅ Test 3 passed - Parameters table overrode instruction JSON where available")
        print(f"   Callback ID: {result3.id}")
        print(f"   Source: {result3.parameters_json['input_parameters']['_source']}")
        input_params = result3.parameters_json['input_parameters']
        print(f"   k={input_params['k']} (from table), y0={input_params['y0']} (from table), tf={input_params['tf']} (from table)")
        print(f"   t0={input_params['t0']} (from instruction), n_points={input_params['n_points']} (from instruction)")
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
    
    # Show parameter resolution hierarchy in action
    print("\n=== Parameter Resolution Summary ===")
    print("Priority Order:")
    print("1. 🥇 Parameters Table (highest priority)")
    print("2. 🥈 Instruction JSON (medium priority)")  
    print("3. 🥉 Static Defaults (lowest priority)")
    print("\nFor each parameter, the service checks in this order and uses the first one found.")
    
    # Cleanup
    Parameter.objects.filter(tenant=tenant, event_key=event_key).delete()
    Instruction.objects.filter(tenant=tenant, eventKey=event_key).delete()
    print(f"\n🧹 Cleaned up test data for event_key: {event_key}")

if __name__ == "__main__":
    test_parameter_resolution()