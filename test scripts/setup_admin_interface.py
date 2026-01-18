#!/usr/bin/env python
"""
Configure django-admin-interface for D.O.S.E. with proper branding
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from admin_interface.models import Theme

def setup_dose_admin_interface():
    """Configure django-admin-interface for D.O.S.E. technology platform."""
    
    print("⚙️ Configuring D.O.S.E. Admin Interface")
    print("=" * 50)
    print("🔧 D.O.S.E. = Dynamic Orchestration Service Engine")
    print("=" * 50)
    
    # Get or create the default theme
    theme, created = Theme.objects.get_or_create(
        name='D.O.S.E. Technology',
        defaults={
            'active': True,
            'title': 'D.O.S.E. Administration',
            'title_visible': True,
            'logo': '',
            'logo_visible': True,
            'env_name': 'Dynamic Orchestration Service Engine',
            'env_visible_in_header': True,
            'env_color': '#007cba',
            'env_visible_in_favicon': False,
            
            # Color scheme - Technology Blue
            'css_header_background_color': '#2c5aa0',
            'css_header_title_color': '#ffffff',
            'css_header_date_color': '#ffffff',
            'css_header_link_color': '#ffffff',
            'css_header_link_hover_color': '#e3f2fd',
            
            'css_module_background_color': '#ffffff',
            'css_module_text_color': '#2c5aa0',
            'css_module_link_color': '#1e3a8a',
            'css_module_link_hover_color': '#3b82f6',
            
            'css_generic_link_color': '#2c5aa0',
            'css_generic_link_hover_color': '#1e3a8a',
            
            'css_save_button_background_color': '#2c5aa0',
            'css_save_button_background_hover_color': '#1e3a8a',
            'css_save_button_text_color': '#ffffff',
            
            'css_delete_button_background_color': '#dc3545',
            'css_delete_button_background_hover_color': '#c82333',
            'css_delete_button_text_color': '#ffffff',
            
            # Sidebar colors
            'css_module_background_selected_color': '#e3f2fd',
            'css_module_selected_bg': '#2c5aa0',
            
            # List styling
            'list_filter_dropdown': True,
            'recent_actions_visible': True,
            'favicon': '',
            'related_modal_active': True,
            'related_modal_background_color': '#000000',
            'related_modal_background_opacity': '0.3',
            'language_chooser_active': False,
            'language_chooser_display': 'code',
            'list_filter_sticky': True,
            'form_submit_sticky': True,
            'form_pagination_sticky': True,
            'collapsible_stacked_inlines': True,
            'collapsible_stacked_inlines_collapsed': False,
            'collapsible_tabular_inlines': True,
            'collapsible_tabular_inlines_collapsed': False
        }
    )
    
    if created:
        print("✅ Created new D.O.S.E. admin theme")
    else:
        print("🔄 Updated existing D.O.S.E. admin theme")
        # Update the theme with latest settings
        theme.title = 'D.O.S.E. Administration'
        theme.env_name = 'Dynamic Orchestration Service Engine'
        theme.active = True
        theme.save()
    
    print(f"\n🎨 Theme Configuration:")
    print(f"  Name: {theme.name}")
    print(f"  Title: {theme.title}")
    print(f"  Environment: {theme.env_name}")
    print(f"  Active: {theme.active}")
    
    # Create additional technology-themed configurations
    tech_themes = [
        {
            'name': 'D.O.S.E. Green Computing',
            'header_color': '#059669',
            'env_name': 'Green Computing Environment',
            'description': 'Natural Computing Theme'
        },
        {
            'name': 'D.O.S.E. Premium Platform', 
            'header_color': '#7c3aed',
            'env_name': 'Premium Platform Environment',
            'description': 'Premium Platform Theme'
        },
        {
            'name': 'D.O.S.E. Dynamic Systems',
            'header_color': '#ea580c', 
            'env_name': 'Dynamic Systems Environment',
            'description': 'Dynamic & Energetic Theme'
        },
        {
            'name': 'D.O.S.E. Industrial',
            'header_color': '#475569',
            'env_name': 'Industrial Computing Environment', 
            'description': 'Industrial Modern Theme'
        }
    ]
    
    created_themes = []
    for theme_config in tech_themes:
        alt_theme, alt_created = Theme.objects.get_or_create(
            name=theme_config['name'],
            defaults={
                'active': False,  # Only one active at a time
                'title': 'D.O.S.E. Administration',
                'title_visible': True,
                'env_name': theme_config['env_name'],
                'env_visible_in_header': True,
                'env_color': theme_config['header_color'],
                'css_header_background_color': theme_config['header_color'],
                'css_header_title_color': '#ffffff',
                'css_save_button_background_color': theme_config['header_color'],
                'css_generic_link_color': theme_config['header_color'],
            }
        )
        if alt_created:
            created_themes.append(theme_config['name'])
    
    if created_themes:
        print(f"\n➕ Created additional theme options:")
        for theme_name in created_themes:
            print(f"  • {theme_name}")
    
    print(f"\n📍 Admin Interface Configuration:")
    print(f"  1. Visit: http://127.0.0.1:8000/admin/admin_interface/theme/")
    print(f"  2. Select and activate different D.O.S.E. themes")
    print(f"  3. Customize colors and branding as needed")
    print(f"  4. View changes immediately in admin interface")
    
    print(f"\n🔧 Integration with Tenant System:")
    print(f"  • django-admin-interface provides site-wide theming")
    print(f"  • Custom tenant themes still available per organization")
    print(f"  • Both systems can work together for maximum flexibility")
    
    print(f"\n✅ D.O.S.E. Admin Interface Ready!")
    print("⚙️ Professional technology platform themes configured!")

if __name__ == "__main__":
    setup_dose_admin_interface()
