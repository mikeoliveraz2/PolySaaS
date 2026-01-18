#!/usr/bin/env python
"""
Sample Navigation Panel Data Setup Script

This script creates sample navigation panels and items for each tenant
to demonstrate the table-driven navigation system.
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import Tenant, NavigationPanel, NavigationItem

def create_sample_navigation():
    """Create sample navigation panels and items for all tenants"""
    
    tenants = Tenant.objects.all()
    if not tenants.exists():
        print("⚠️  No tenants found. Please create at least one tenant first.")
        return
    
    for tenant in tenants:
        print(f"\n🏢 Creating navigation for {tenant.name}...")
        
        # 1. Quick Actions Panel
        quick_actions, created = NavigationPanel.objects.get_or_create(
            tenant=tenant,
            title="Quick Actions",
            defaults={
                'panel_type': 'quick_actions',
                'description': 'Common tasks and shortcuts for daily workflow',
                'sort_order': 10,
                'is_active': True
            }
        )
        
        if created:
            # Quick Actions Items
            NavigationItem.objects.create(
                panel=quick_actions,
                title="Create Task",
                item_type="internal",
                url="http://localhost:8000/admin/dose/task/add/",
                description="Create a new task in the system",
                icon_style="emoji",
                icon_value="📝",
                sort_order=10
            )
            
            NavigationItem.objects.create(
                panel=quick_actions,
                title="Add Instruction",
                item_type="internal",
                url="http://localhost:8000/admin/dose/instruction/add/",
                description="Add a new system instruction",
                icon_style="emoji",
                icon_value="⚙️",
                sort_order=20
            )
            
            NavigationItem.objects.create(
                panel=quick_actions,
                title="View Dashboard",
                item_type="internal",
                url="http://localhost:8000/dose/",
                description="Go to main dashboard",
                icon_style="emoji",
                icon_value="📊",
                sort_order=30
            )
            
            print(f"  ✅ Created Quick Actions panel with 3 items")
        
        # 2. System Integrations Panel
        integrations, created = NavigationPanel.objects.get_or_create(
            tenant=tenant,
            title="System Integrations",
            defaults={
                'panel_type': 'integrations',
                'description': 'External systems and API connections',
                'sort_order': 20,
                'is_active': True,
                'panel_background_color': '#f8f9fa'
            }
        )
        
        if created:
            # Integration Items
            NavigationItem.objects.create(
                panel=integrations,
                title="Customer Portal",
                item_type="link",
                url="https://customer.example.com",
                description="Access external customer management system",
                icon_style="emoji",
                icon_value="🏢",
                target="_blank",
                sort_order=10
            )
            
            NavigationItem.objects.create(
                panel=integrations,
                title="API Documentation",
                item_type="link",
                url="https://api.example.com/docs",
                description="View API documentation and endpoints",
                icon_style="emoji",
                icon_value="📚",
                target="_blank",
                sort_order=20
            )
            
            NavigationItem.objects.create(
                panel=integrations,
                title="Monitoring Dashboard",
                item_type="link",
                url="https://monitoring.example.com",
                description="System health and performance monitoring",
                icon_style="emoji",
                icon_value="📈",
                target="_blank",
                sort_order=30
            )
            
            print(f"  ✅ Created System Integrations panel with 3 items")
        
        # 3. Analytics & Reports Panel
        analytics, created = NavigationPanel.objects.get_or_create(
            tenant=tenant,
            title="Analytics & Reports",
            defaults={
                'panel_type': 'analytics',
                'description': 'Data insights and reporting tools',
                'sort_order': 30,
                'is_active': True
            }
        )
        
        if created:
            # Analytics Items
            NavigationItem.objects.create(
                panel=analytics,
                title="Usage Report",
                item_type="internal",
                url="/dose/reports/usage/",
                description="System usage and activity report",
                icon_style="emoji",
                icon_value="📊",
                sort_order=10
            )
            
            NavigationItem.objects.create(
                panel=analytics,
                title="Performance Metrics",
                item_type="internal",
                url="/dose/reports/performance/",
                description="System performance and response time metrics",
                icon_style="emoji",
                icon_value="⚡",
                sort_order=20
            )
            
            NavigationItem.objects.create(
                panel=analytics,
                title="Export Data",
                item_type="download",
                url="/dose/export/csv/",
                description="Download data export in CSV format",
                icon_style="emoji",
                icon_value="📥",
                sort_order=30
            )
            
            print(f"  ✅ Created Analytics & Reports panel with 3 items")
        
        # 4. Administration Panel (only for specific tenants)
        if tenant.name in ['Default Tenant', 'Admin']:
            admin_panel, created = NavigationPanel.objects.get_or_create(
                tenant=tenant,
                title="System Administration",
                defaults={
                    'panel_type': 'administration',
                    'description': 'System settings and user management',
                    'sort_order': 40,
                    'is_active': True
                }
            )
            
            if created:
                # Admin Items
                NavigationItem.objects.create(
                    panel=admin_panel,
                    title="User Management",
                    item_type="internal",
                    url="/admin/auth/user/",
                    description="Manage system users",
                    icon_style="emoji",
                    icon_value="👥",
                    requires_permissions="auth.change_user",
                    sort_order=10
                )
                
                NavigationItem.objects.create(
                    panel=admin_panel,
                    title="Tenant Settings",
                    item_type="internal",
                    url="/admin/dose/tenant/",
                    description="Manage tenant configurations",
                    icon_style="emoji",
                    icon_value="🏢",
                    requires_permissions="dose.change_tenant",
                    sort_order=20
                )
                
                print(f"  ✅ Created System Administration panel with 2 items")
        
        # 5. Custom Panel for specific tenant
        if tenant.slug == 'acme-corp':
            custom_panel, created = NavigationPanel.objects.get_or_create(
                tenant=tenant,
                title="ACME Custom Tools",
                defaults={
                    'panel_type': 'custom',
                    'description': 'Custom tools and integrations for ACME Corp',
                    'sort_order': 50,
                    'is_active': True,
                    'panel_background_color': '#fff3cd'
                }
            )
            
            if created:
                # Custom Items
                NavigationItem.objects.create(
                    panel=custom_panel,
                    title="ACME CRM",
                    item_type="link",
                    url="https://crm.acme.com",
                    description="Access ACME customer relationship management",
                    icon_style="emoji",
                    icon_value="🎯",
                    target="_blank",
                    sort_order=10
                )
                
                NavigationItem.objects.create(
                    panel=custom_panel,
                    title="Email Support",
                    item_type="mailto",
                    url="mailto:support@acme.com?subject=D.O.S.E. Support Request",
                    description="Contact ACME support team",
                    icon_style="emoji",
                    icon_value="📧",
                    target="_self",
                    sort_order=20
                )
                
                print(f"  ✅ Created ACME Custom Tools panel with 2 items")

def display_navigation_summary():
    """Display a summary of created navigation panels"""
    print("\n" + "="*60)
    print("📊 NAVIGATION PANELS SUMMARY")
    print("="*60)
    
    for tenant in Tenant.objects.all():
        panels = NavigationPanel.objects.filter(tenant=tenant, is_active=True)
        total_items = NavigationItem.objects.filter(panel__tenant=tenant, is_active=True).count()
        
        print(f"\n🏢 {tenant.name} ({tenant.slug})")
        print(f"   Panels: {panels.count()} | Active Items: {total_items}")
        
        for panel in panels.order_by('sort_order'):
            item_count = panel.navigation_items.filter(is_active=True).count()
            print(f"   └─ {panel.title} ({panel.panel_type}) - {item_count} items")

if __name__ == "__main__":
    print("🚀 D.O.S.E. Navigation Panel Setup")
    print("="*50)
    
    try:
        create_sample_navigation()
        display_navigation_summary()
        
        print("\n" + "="*60)
        print("✅ SETUP COMPLETE!")
        print("="*60)
        print("Next steps:")
        print("1. Check the admin interface at /admin/dose/navigationpanel/")
        print("2. Customize navigation items for your tenants")
        print("3. Update the landing page template to display navigation panels")
        print("4. Test the navigation links and functionality")
        
    except Exception as e:
        print(f"\n❌ Error creating navigation data: {e}")
        import traceback
        traceback.print_exc()
