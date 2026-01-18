#!/usr/bin/env python
"""
Test script for enhanced HelloWorld atomic service
Usage: python manage.py shell < test_helloworld_service.py
Or: python test_helloworld_service.py
"""

import os
import sys
import django
from django.test import RequestFactory
from django.contrib.auth.models import User, AnonymousUser

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.services.HelloWorld_eB0QUGW import HelloWorld
from dose.models import Tenant, Instruction, CallBackData, DoseMessage

print("\n" + "="*80)
print("HELLOWORLD ATOMIC SERVICE TEST SUITE")
print("="*80 + "\n")

# Test 1: Basic execution with authenticated user
print("TEST 1: Basic Execution with Authenticated User")
print("-" * 80)

factory = RequestFactory()
request = factory.get('/')

try:
    user = User.objects.filter(username='olientAdmin').first()
    if not user:
        print("⚠️  User 'olientAdmin' not found. Creating test user...")
        user = User.objects.create_user(username='testuser', email='test@dose.local')

    tenant = Tenant.objects.filter(name__icontains='oliver').first()
    if not tenant:
        print("⚠️  Oliver Enterprises tenant not found. Using first available tenant...")
        tenant = Tenant.objects.first()

    if not tenant:
        print("❌ No tenant available. Please create a tenant first.")
        sys.exit(1)

    request.user = user
    request.tenant = tenant

    print(f"✅ User: {user.username}")
    print(f"✅ Tenant: {tenant.name}")

    # Execute service
    result = HelloWorld.execute_and_save(request, None)

    print(f"\n📊 Service Result:")
    print(f"  - Username: {result.get('username')}")
    print(f"  - Tenant: {result.get('tenant_name')}")
    print(f"  - Status: {result.get('execution_status')}")
    print(f"  - Greeting: {result.get('greeting')[:60]}...")

    assert result['username'] == user.username, "Username mismatch"
    assert result['tenant_name'] == tenant.name, "Tenant name mismatch"
    assert result['execution_status'] == 'success', "Execution status not success"
    assert 'greeting' in result, "Greeting missing from result"

    print("\n✅ TEST 1 PASSED\n")

except Exception as e:
    print(f"\n❌ TEST 1 FAILED: {str(e)}\n")
    import traceback
    traceback.print_exc()

# Test 2: Execution with CallBackData persistence
print("\nTEST 2: Execution with CallBackData Persistence")
print("-" * 80)

try:
    # Create instruction with save_callbackdata enabled
    instruction = Instruction.objects.create(
        tenant=tenant,
        eventKey='test_greeting_event',
        requestpath='/test/hello/',
        requestmethod='GET',
        executescript='HelloWorld',
        description='Test HelloWorld Greeting',
        save_callbackdata=True
    )

    print(f"✅ Created instruction: {instruction.eventKey}")

    # Reset request
    request = factory.get('/')
    request.user = user
    request.tenant = tenant

    # Execute service
    result = HelloWorld.execute_and_save(request, instruction)

    print(f"✅ Service executed successfully")

    # Verify CallBackData was created
    cb = CallBackData.objects.filter(
        tenant=tenant,
        matchingEventKey='test_greeting_event'
    ).latest('pub_date')

    print(f"✅ CallBackData created: {cb.id}")
    print(f"  - Description: {cb.description}")
    print(f"  - Parameters: {str(cb.parameters_json)[:80]}...")

    assert cb is not None, "CallBackData not found"
    assert user.username in cb.description, "Username not in description"

    print("\n✅ TEST 2 PASSED\n")

except Exception as e:
    print(f"\n❌ TEST 2 FAILED: {str(e)}\n")
    import traceback
    traceback.print_exc()

# Test 3: Execution with anonymous user
print("\nTEST 3: Execution with Anonymous User")
print("-" * 80)

try:
    request = factory.get('/')
    request.user = AnonymousUser()
    request.tenant = tenant

    print(f"✅ Using anonymous user")

    # Execute service
    result = HelloWorld.execute_and_save(request, None)

    print(f"\n📊 Service Result:")
    print(f"  - Username: {result.get('username')}")
    print(f"  - Tenant: {result.get('tenant_name')}")
    print(f"  - Greeting: {result.get('greeting')[:60]}...")

    assert result['username'] == 'Guest', "Username should be 'Guest' for anonymous user"
    assert 'Guest' in result['greeting'], "Guest not in greeting"

    print("\n✅ TEST 3 PASSED\n")

except Exception as e:
    print(f"\n❌ TEST 3 FAILED: {str(e)}\n")
    import traceback
    traceback.print_exc()

# Test 4: DoseMessage creation verification
print("\nTEST 4: DoseMessage Creation Verification")
print("-" * 80)

try:
    request = factory.get('/')
    request.user = user
    request.tenant = tenant

    # Count messages before
    msg_count_before = DoseMessage.objects.count()

    # Execute service
    result = HelloWorld.execute_and_save(request, None)

    # Count messages after
    msg_count_after = DoseMessage.objects.count()

    print(f"✅ Messages before: {msg_count_before}")
    print(f"✅ Messages after: {msg_count_after}")

    assert msg_count_after > msg_count_before, "DoseMessage not created"

    # Get the latest message
    latest_msg = DoseMessage.objects.latest('id')
    print(f"✅ Latest message: {latest_msg.message[:60]}...")
    print(f"  - Level: {latest_msg.level}")
    print(f"  - User: {latest_msg.user}")

    assert latest_msg.level == 'success', "Message level not 'success'"
    assert user.username in latest_msg.message, "Username not in message"

    print("\n✅ TEST 4 PASSED\n")

except Exception as e:
    print(f"\n❌ TEST 4 FAILED: {str(e)}\n")
    import traceback
    traceback.print_exc()

# Test 5: Parameter fetching
print("\nTEST 5: Parameter Fetching")
print("-" * 80)

try:
    # Test with dict parameters
    test_params = {'MatchingKey': 'HelloWorld', 'value': 'test'}
    result = HelloWorld.get_parameters(test_params)
    print(f"✅ Dict parameter fetch: {result}")
    assert result == test_params, "Dict parameter fetch failed"

    # Test with non-matching dict
    non_matching = {'MatchingKey': 'OtherService', 'value': 'test'}
    result = HelloWorld.get_parameters(non_matching)
    print(f"✅ Non-matching dict returns: {result}")
    assert result is None, "Non-matching should return None"

    print("\n✅ TEST 5 PASSED\n")

except Exception as e:
    print(f"\n❌ TEST 5 FAILED: {str(e)}\n")
    import traceback
    traceback.print_exc()

# Summary
print("="*80)
print("TEST SUITE COMPLETE")
print("="*80)
print("\n✅ All tests completed. Check results above.\n")

# Cleanup
print("\nCleaning up test data...")
try:
    Instruction.objects.filter(eventKey='test_greeting_event').delete()
    print("✅ Test instruction deleted")
except Exception as e:
    print(f"⚠️  Cleanup warning: {e}")

print("\n" + "="*80)
print("Ready to proceed with next atomic service enhancement!")
print("="*80 + "\n")
