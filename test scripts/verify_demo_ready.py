"""
Quick demo readiness check
Verifies Gmail and OSTicket passthrough are configured
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassthroughEndpoint
from django.contrib.auth.models import User

def main():
    print("\n" + "="*70)
    print("DEMO READINESS CHECK - OSTicket & Gmail")
    print("="*70)

    # Check PassthroughEndpoints
    print("\n📊 Passthrough Endpoints:")
    endpoints = PassthroughEndpoint.objects.filter(is_enabled=True)

    if endpoints.count() == 0:
        print("   ❌ NO ENDPOINTS CONFIGURED!")
        return

    osticket_ready = False
    gmail_ready = False

    for ep in endpoints:
        status = "✅" if ep.show_in_menu else "⚠️ (hidden)"
        print(f"\n   {status} {ep.name}")
        print(f"      Trigger: {ep.trigger_path}")
        print(f"      Target: {ep.endpoint_url}")
        print(f"      Menu: {ep.show_in_menu}")
        print(f"      Enabled: {ep.is_enabled}")

        if 'osticket' in ep.name.lower() or 'osticket' in ep.trigger_path.lower():
            osticket_ready = True
            print(f"      🎯 OSTicket READY for demo")

        if 'gmail' in ep.name.lower() or 'gmail' in ep.trigger_path.lower():
            gmail_ready = True
            print(f"      📧 Gmail READY (needs re-auth)")

    # Check user
    print("\n👤 Demo User:")
    try:
        user = User.objects.get(username='olientAdmin')
        print(f"   ✅ {user.username} - Staff: {user.is_staff}, Active: {user.is_active}")
    except User.DoesNotExist:
        print("   ❌ olientAdmin not found!")

    # Summary
    print("\n" + "="*70)
    print("DEMO STATUS:")
    print("="*70)
    print(f"{'✅' if osticket_ready else '❌'} OSTicket: {'READY' if osticket_ready else 'NOT CONFIGURED'}")
    print(f"{'⚠️' if gmail_ready else '❌'} Gmail: {'READY (needs re-auth)' if gmail_ready else 'NOT CONFIGURED'}")

    if osticket_ready:
        print("\n🎯 OSTicket Demo Flow:")
        print("   1. Click 'OsTicket' in top menu")
        print("   2. Should see OSTicket login or dashboard")
        print("   3. Full passthrough - no iframes!")

    if gmail_ready:
        print("\n📧 Gmail Demo Flow:")
        print("   1. Click 'Gmail' in top menu")
        print("   2. Click 'Connect Google Account'")
        print("   3. Grant Gmail permissions")
        print("   4. See inbox!")

    print("="*70 + "\n")

if __name__ == '__main__':
    main()
