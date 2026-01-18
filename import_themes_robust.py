#!/usr/bin/env python
"""
Robust import of D.O.S.E. themes with proper field validation
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from admin_interface.models import Theme

def get_safe_fields():
    """Get only the fields that actually exist in the Theme model."""
    theme_fields = {f.name: f for f in Theme._meta.fields}
    
    # Core fields that should always exist
    safe_defaults = {
        'active': False,
        'name': '',
        'title': 'D.O.S.E. Administration',
    }
    
    # Add optional fields if they exist
    optional_fields = {
        'title_visible': True,
        'title_color': '#ffffff',
        'env_name': '',
        'env_visible_in_header': True, 
        'env_color': '#2c5aa0',
        'css_header_background_color': '#2c5aa0',
        'css_header_title_color': '#ffffff',
        'css_header_date_color': '#ffffff',
        'css_header_link_color': '#ffffff',
        'css_header_link_hover_color': '#e3f2fd',
        'css_module_background_color': '#ffffff',
        'css_module_text_color': '#2c5aa0',
        'css_module_link_color': '#1e40af',
        'css_module_link_hover_color': '#3b82f6',
        'css_generic_link_color': '#2c5aa0',
        'css_generic_link_hover_color': '#1e40af',
        'css_save_button_background_color': '#2c5aa0',
        'css_save_button_background_hover_color': '#1e40af',
        'css_save_button_text_color': '#ffffff',
        'css_delete_button_background_color': '#dc3545',
        'css_delete_button_background_hover_color': '#c82333',
        'css_delete_button_text_color': '#ffffff',
        'list_filter_dropdown': True,
        'recent_actions_visible': True,
        'related_modal_active': True,
        'related_modal_background_color': '#000000',
        'related_modal_background_opacity': '0.3',
        'list_filter_sticky': True,
        'form_submit_sticky': True,
    }
    
    # Only add fields that actually exist
    for field_name, value in optional_fields.items():
        if field_name in theme_fields:
            safe_defaults[field_name] = value
    
    return safe_defaults, theme_fields.keys()

def import_dose_themes_safe():
    """Import D.O.S.E. themes using only validated fields."""
    
    print("🔧 Robust D.O.S.E. Theme Import")
    print("=" * 40)
    print("⚙️ D.O.S.E. = Dynamic Orchestration Service Engine")
    print("=" * 40)
    
    safe_defaults, available_fields = get_safe_fields()
    
    print(f"✅ Validated {len(safe_defaults)} safe fields")
    print(f"📋 Available model fields: {len(available_fields)}")
    
    # Define themes with basic info
    themes_to_create = [
        {
            'name': 'D.O.S.E. Tech Blue',
            'env_name': 'Technology Platform',
            'primary_color': '#2c5aa0',
            'secondary_color': '#1e40af',
            'accent_color': '#3b82f6'
        },
        {
            'name': 'D.O.S.E. Forest Green',
            'env_name': 'Green Computing',
            'primary_color': '#059669',
            'secondary_color': '#065f46', 
            'accent_color': '#10b981'
        },
        {
            'name': 'D.O.S.E. Royal Purple',
            'env_name': 'Premium Platform',
            'primary_color': '#7c3aed',
            'secondary_color': '#5b21b6',
            'accent_color': '#8b5cf6'
        },
        {
            'name': 'D.O.S.E. Sunset Orange',
            'env_name': 'Dynamic Systems', 
            'primary_color': '#ea580c',
            'secondary_color': '#b91c1c',
            'accent_color': '#f97316'
        },
        {
            'name': 'D.O.S.E. Steel Gray',
            'env_name': 'Industrial Computing',
            'primary_color': '#475569',
            'secondary_color': '#1f2937',
            'accent_color': '#64748b'
        }
    ]
    
    created_count = 0
    updated_count = 0
    
    for theme_def in themes_to_create:
        print(f"\n🎨 Processing: {theme_def['name']}")
        
        # Start with safe defaults
        theme_data = safe_defaults.copy()
        theme_data['name'] = theme_def['name']
        
        # Add environment name if field exists
        if 'env_name' in available_fields:
            theme_data['env_name'] = theme_def['env_name']
        
        # Apply colors to available color fields
        color_mappings = {
            'css_header_background_color': theme_def['primary_color'],
            'css_generic_link_color': theme_def['primary_color'], 
            'css_save_button_background_color': theme_def['primary_color'],
            'css_module_link_color': theme_def['secondary_color'],
            'css_generic_link_hover_color': theme_def['secondary_color'],
            'css_save_button_background_hover_color': theme_def['secondary_color'],
            'css_module_link_hover_color': theme_def['accent_color'],
            'env_color': theme_def['primary_color'],
        }
        
        for field_name, color in color_mappings.items():
            if field_name in available_fields:
                theme_data[field_name] = color
        
        try:
            # Remove 'name' from defaults since it's used in get_or_create
            create_data = {k: v for k, v in theme_data.items() if k != 'name'}
            
            theme, created = Theme.objects.get_or_create(
                name=theme_def['name'],
                defaults=create_data
            )
            
            if created:
                created_count += 1
                print(f"  ✅ Created successfully")
            else:
                # Update existing theme
                for field_name, value in create_data.items():
                    if hasattr(theme, field_name):
                        setattr(theme, field_name, value)
                theme.save()
                updated_count += 1
                print(f"  🔄 Updated existing theme")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Show results
    print(f"\n📊 Import Results:")
    print(f"  🆕 Created: {created_count} themes")
    print(f"  🔄 Updated: {updated_count} themes")
    
    # List all D.O.S.E. themes
    all_dose_themes = Theme.objects.filter(name__startswith='D.O.S.E.').order_by('name')
    print(f"\n🎨 All D.O.S.E. Themes ({all_dose_themes.count()}):")
    
    for theme in all_dose_themes:
        status = "🟢 ACTIVE" if theme.active else "⚪ Inactive"
        print(f"  • {theme.name}: {status}")
    
    if all_dose_themes.count() == 0:
        print("  ⚠️  No D.O.S.E. themes found!")
        print("  💡 There may be field validation issues")
    
    print(f"\n🔍 Debug Info:")
    print(f"  Total themes in database: {Theme.objects.count()}")
    print(f"  Fields validated: {len(safe_defaults)}")
    
    print(f"\n📍 Next Steps:")
    print(f"  1. Visit: http://127.0.0.1:8000/admin/admin_interface/theme/")
    print(f"  2. You should now see {5 + created_count + updated_count} or more D.O.S.E. themes")
    print(f"  3. Activate any theme to test it")
    
    print(f"\n✅ Robust import complete!")

if __name__ == "__main__":
    import_dose_themes_safe()
