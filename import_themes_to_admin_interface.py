#!/usr/bin/env python
"""
Import manual D.O.S.E. themes into django-admin-interface
"""
import os
import django
import re

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from admin_interface.models import Theme

def extract_css_colors(css_file_path):
    """Extract color values from CSS file."""
    colors = {}
    
    try:
        with open(css_file_path, 'r') as f:
            content = f.read()
            
        # Extract gradient colors from CSS
        gradient_matches = re.findall(r'linear-gradient\([^)]+\)', content)
        if gradient_matches:
            # Extract hex colors from first gradient
            hex_colors = re.findall(r'#[0-9a-fA-F]{6}', gradient_matches[0])
            if hex_colors:
                colors['primary'] = hex_colors[0]
                colors['secondary'] = hex_colors[-1]
        
        # Extract individual hex colors
        all_hex = re.findall(r'#[0-9a-fA-F]{6}', content)
        if all_hex:
            colors['primary'] = colors.get('primary', all_hex[0])
            colors['accent'] = all_hex[1] if len(all_hex) > 1 else colors['primary']
            
    except Exception as e:
        print(f"  ⚠️  Error reading {css_file_path}: {e}")
        
    return colors

def import_dose_themes():
    """Import all manual D.O.S.E. themes into admin-interface."""
    
    print("🎨 Importing D.O.S.E. Themes into Admin Interface")
    print("=" * 55)
    print("⚙️ D.O.S.E. = Dynamic Orchestration Service Engine")
    print("=" * 55)
    
    # Define the manual themes with their details
    theme_definitions = [
        {
            'name': 'D.O.S.E. Tech Blue',
            'css_file': 'static/admin/css/theme_tech_blue.css',
            'description': 'Professional Technology Platform',
            'icon': '💻',
            'env_name': 'Technology Platform',
            'default_colors': {'primary': '#2c5aa0', 'secondary': '#1e40af', 'accent': '#3b82f6'}
        },
        {
            'name': 'D.O.S.E. Forest Green', 
            'css_file': 'static/admin/css/theme_forest_green.css',
            'description': 'Natural Computing Environment',
            'icon': '🌲',
            'env_name': 'Green Computing',
            'default_colors': {'primary': '#059669', 'secondary': '#065f46', 'accent': '#10b981'}
        },
        {
            'name': 'D.O.S.E. Royal Purple',
            'css_file': 'static/admin/css/theme_royal_purple.css', 
            'description': 'Premium Platform Experience',
            'icon': '🔮',
            'env_name': 'Premium Platform',
            'default_colors': {'primary': '#7c3aed', 'secondary': '#5b21b6', 'accent': '#8b5cf6'}
        },
        {
            'name': 'D.O.S.E. Sunset Orange',
            'css_file': 'static/admin/css/theme_sunset_orange.css',
            'description': 'Dynamic & Energetic Systems',
            'icon': '🔥', 
            'env_name': 'Dynamic Systems',
            'default_colors': {'primary': '#ea580c', 'secondary': '#b91c1c', 'accent': '#f97316'}
        },
        {
            'name': 'D.O.S.E. Steel Gray',
            'css_file': 'static/admin/css/theme_steel_gray.css',
            'description': 'Industrial Modern Computing',
            'icon': '⚙️',
            'env_name': 'Industrial Computing',
            'default_colors': {'primary': '#475569', 'secondary': '#1f2937', 'accent': '#64748b'}
        }
    ]
    
    imported_themes = []
    updated_themes = []
    
    for theme_def in theme_definitions:
        print(f"\n{theme_def['icon']} Processing: {theme_def['name']}")
        
        # Extract colors from CSS file
        css_colors = extract_css_colors(theme_def['css_file'])
        if not css_colors:
            css_colors = theme_def['default_colors']
            print(f"  📄 Using default colors (CSS file not found)")
        else:
            print(f"  📄 Extracted colors from CSS file")
        
        # Create or update the theme
        try:
            theme, created = Theme.objects.get_or_create(
                name=theme_def['name'],
                defaults={
                    'active': False,  # Only activate one at a time
                    'title': 'D.O.S.E. Administration',
                    'title_visible': True,
                    'title_color': '#ffffff',
                    'env_name': theme_def['env_name'],
                    'env_visible_in_header': True,
                    'env_color': css_colors.get('primary', '#2c5aa0'),
                    
                    # Header colors
                    'css_header_background_color': css_colors.get('primary', '#2c5aa0'),
                    'css_header_title_color': '#ffffff',
                    'css_header_date_color': '#ffffff',
                    'css_header_link_color': '#ffffff',
                    'css_header_link_hover_color': '#e3f2fd',
                    
                    # Module colors  
                    'css_module_background_color': '#ffffff',
                    'css_module_text_color': css_colors.get('primary', '#2c5aa0'),
                    'css_module_link_color': css_colors.get('secondary', '#1e40af'),
                    'css_module_link_hover_color': css_colors.get('accent', '#3b82f6'),
                    
                    # Generic link colors
                    'css_generic_link_color': css_colors.get('primary', '#2c5aa0'),
                    'css_generic_link_hover_color': css_colors.get('secondary', '#1e40af'),
                    
                    # Button colors
                    'css_save_button_background_color': css_colors.get('primary', '#2c5aa0'),
                    'css_save_button_background_hover_color': css_colors.get('secondary', '#1e40af'),
                    'css_save_button_text_color': '#ffffff',
                    
                    'css_delete_button_background_color': '#dc3545',
                    'css_delete_button_background_hover_color': '#c82333',
                    'css_delete_button_text_color': '#ffffff',
                    
                    # Interface options
                    'list_filter_dropdown': True,
                    'recent_actions_visible': True,
                    'related_modal_active': True,
                    'related_modal_background_color': '#000000',
                    'related_modal_background_opacity': '0.3',
                    'list_filter_sticky': True,
                    'form_submit_sticky': True,
                }
            )
            
            if created:
                imported_themes.append(theme_def['name'])
                print(f"  ✅ Imported as new theme")
            else:
                # Update existing theme with new colors
                theme.css_header_background_color = css_colors.get('primary', theme.css_header_background_color)
                theme.css_generic_link_color = css_colors.get('primary', theme.css_generic_link_color) 
                theme.css_save_button_background_color = css_colors.get('primary', theme.css_save_button_background_color)
                theme.env_name = theme_def['env_name']
                theme.save()
                updated_themes.append(theme_def['name'])
                print(f"  🔄 Updated existing theme")
                
            print(f"     Primary: {css_colors.get('primary', 'default')}")
            print(f"     Secondary: {css_colors.get('secondary', 'default')}")
            
        except Exception as e:
            print(f"  ❌ Error importing {theme_def['name']}: {e}")
    
    # Summary
    print(f"\n📊 Import Summary:")
    print(f"  🆕 New themes imported: {len(imported_themes)}")
    print(f"  🔄 Existing themes updated: {len(updated_themes)}")
    
    if imported_themes:
        print(f"\n✅ Imported Themes:")
        for theme_name in imported_themes:
            print(f"  • {theme_name}")
            
    if updated_themes:
        print(f"\n🔄 Updated Themes:")
        for theme_name in updated_themes:
            print(f"  • {theme_name}")
    
    # Show all available themes
    print(f"\n🎨 All Available D.O.S.E. Themes:")
    all_themes = Theme.objects.filter(name__startswith='D.O.S.E.').order_by('name')
    
    for theme in all_themes:
        status = "🟢 Active" if theme.active else "⚪ Inactive"
        print(f"  • {theme.name}: {status}")
    
    print(f"\n📍 How to Use:")
    print(f"  1. Visit: http://127.0.0.1:8000/admin/admin_interface/theme/")
    print(f"  2. Select any D.O.S.E. theme from the list")
    print(f"  3. Set as 'Active' to apply site-wide")
    print(f"  4. Customize colors further if desired") 
    print(f"  5. Save and see immediate changes!")
    
    print(f"\n🎯 Benefits of Admin Interface Themes:")
    print(f"  ✅ GUI-based theme management")
    print(f"  ✅ Live color picker interface") 
    print(f"  ✅ Professional theme persistence")
    print(f"  ✅ Easy switching between themes")
    print(f"  ✅ Advanced customization options")
    
    print(f"\n🚀 D.O.S.E. themes successfully imported!")
    print("⚙️ Your manual themes are now professional admin-interface themes!")

if __name__ == "__main__":
    import_dose_themes()
