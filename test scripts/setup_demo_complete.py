#!/usr/bin/env python
"""
Complete Demo Setup Script
Sets up:
1. Demo passthrough endpoint (shows in sidebar)
2. Instruction to intercept OSTicket ticket creation
3. Atomic service that posts to Flask service on port 5000
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint, Instruction
from dose.utils import get_current_tenant

def setup_demo_endpoint():
    """Update Monitor Logger endpoint to show in sidebar"""
    endpoint = PassThroughEndpoint.objects.filter(trigger_path='monitor-logger').first()

    if not endpoint:
        print("ERROR: Monitor Logger endpoint not found. Run setup_demo_endpoint.py first!")
        return None

    # Update to show in sidebar
    endpoint.show_in_menu = True
    endpoint.menu_title = 'Monitor Logger'
    endpoint.menu_icon = '📊'
    endpoint.description = 'Real-time monitoring and logging service - intercepts and logs events'
    endpoint.save()

    print("Monitor Logger endpoint updated to show in sidebar")
    return endpoint

def setup_osticket_instruction():
    """Create Instruction to intercept OSTicket ticket creation POST"""

    # OSTicket ticket creation can happen at various paths:
    # - /admin/osticket/scp/tickets.php (main ticket creation)
    # - /admin/osticket/scp/open.php (open new ticket)
    # We'll match any POST containing 'tickets' or 'open' in the path
    # The matching logic uses substring matching, so this will catch variations
    requestpath = '/admin/osticket/scp/tickets.php'  # Primary path

    # Check if instruction already exists
    existing = Instruction.objects.filter(
        requestpath=requestpath,
        requestmethod='POST',
        direction='REQ'
    ).first()

    if existing:
        print(f"✅ Instruction already exists for {requestpath}")
        print(f"   ID: {existing.id}")
        print(f"   Execute Script: {existing.executescript}")
        print(f"   URL List: {existing.urllist}")
        return existing

    # Create new instruction
    instruction = Instruction.objects.create(
        requestpath=requestpath,
        requestmethod='POST',
        direction='REQ',
        executescript='TicketInterceptorService',  # We'll create this atomic service
        urllist='http://localhost:5000/tickets',  # POST to Flask service
        description='Intercept OSTicket ticket creation and forward to Monitor Logger service',
        save_callbackdata=True,  # Save to CallBackData
        eventKey='osticket_ticket_created',
    )

    print("Instruction created for OSTicket ticket interception")
    print(f"   Path: {requestpath}")
    print(f"   Method: POST")
    print(f"   Execute Script: {instruction.executescript}")
    print(f"   URL List: {instruction.urllist}")
    print(f"   Event Key: {instruction.eventKey}")

    return instruction

if __name__ == '__main__':
    print("="*60)
    print("Setting up Complete Demo")
    print("="*60)
    print()

    # Step 1: Update demo endpoint
    endpoint = setup_demo_endpoint()
    if not endpoint:
        exit(1)

    print()

    # Step 2: Create instruction for OSTicket interception
    instruction = setup_osticket_instruction()

    print()
    print("="*60)
    print("Setup complete!")
    print("="*60)
    print()
    print("Next steps:")
    print("1. Create atomic service: TicketInterceptorService")
    print("2. Update Flask service to handle /tickets endpoint")
    print("3. Test by creating a ticket in OSTicket")

