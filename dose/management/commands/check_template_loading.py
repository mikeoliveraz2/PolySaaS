"""
Check which templates are being loaded and their inheritance chain.
Usage: python manage.py check_template_loading
"""
from django.core.management.base import BaseCommand
from django.template import engines
from django.template.loader import get_template


class Command(BaseCommand):
    help = 'Check template loading and inheritance'

    def handle(self, *args, **options):
        self.stdout.write("=== Template Loading Check ===\n")
        
        engine = engines['django']
        
        # Check base templates
        templates_to_check = [
            'admin/base.html',
            'admin/base_site.html',
            'admin/change_form.html',
            'admin/auth/user/change_form.html',
        ]
        
        for template_name in templates_to_check:
            try:
                template = engine.get_template(template_name)
                self.stdout.write(f"\n{template_name}:")
                self.stdout.write(f"  Origin: {template.origin}")
                
                # Get template source to check blocks
                if hasattr(template, 'template') and hasattr(template.template, 'source'):
                    source = template.template.source
                    blocks = []
                    if '{% block page_content %}' in source:
                        blocks.append('page_content')
                    if '{% block content %}' in source:
                        blocks.append('content')
                    if '{{ block.super }}' in source:
                        blocks.append('block.super')
                    if blocks:
                        self.stdout.write(f"  Contains: {', '.join(blocks)}")
                    
                    # Check extends
                    if '{% extends' in source:
                        extends_line = [line for line in source.split('\n') if '{% extends' in line][0]
                        self.stdout.write(f"  {extends_line.strip()}")
                        
            except Exception as e:
                self.stdout.write(f"\n{template_name}: ERROR - {e}")
        
        # Try to render the change_form and see what happens
        self.stdout.write("\n\n=== Rendering Test ===")
        try:
            from django.test import RequestFactory
            from django.contrib.auth.models import User
            
            factory = RequestFactory()
            request = factory.get('/admin/auth/user/1/change/')
            
            # Create a mock request with necessary attributes
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            template = engine.get_template('admin/change_form.html')
            
            # Try to get the rendered content length
            self.stdout.write(f"Template loaded successfully: {template.origin}")
            
        except Exception as e:
            self.stdout.write(f"Rendering test error: {e}")
            import traceback
            traceback.print_exc()
