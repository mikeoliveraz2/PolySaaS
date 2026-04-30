from django.core.management.base import BaseCommand
from django.template import engines
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.contrib.admin.sites import AdminSite


class Command(BaseCommand):
    help = 'Debug template loading for admin pages'

    def handle(self, *args, **options):
        self.stdout.write("=== Template Loading Debug ===")
        
        # Get the Django template engine
        engine = engines['django']
        
        # Try to load the change_form template
        try:
            template = engine.get_template('admin/auth/user/change_form.html')
            self.stdout.write(f"Change form template origin: {template.origin}")
            self.stdout.write(f"Change form template name: {template.template.name}")
            
            # Check if the template has the expected blocks
            if hasattr(template, 'template'):
                source = template.template.source
                if 'block content' in source:
                    self.stdout.write("✓ Change form has 'content' block")
                if 'block page_content' in source:
                    self.stdout.write("✓ Change form has 'page_content' block")
                    
        except Exception as e:
            self.stdout.write(f"Error loading change_form template: {e}")
            import traceback
            traceback.print_exc()
        
        # Check which base.html is being used
        try:
            base_template = engine.get_template('admin/base.html')
            self.stdout.write(f"\nBase template origin: {base_template.origin}")
            self.stdout.write(f"Base template name: {base_template.template.name}")
            
            if hasattr(base_template, 'template'):
                source = base_template.template.source
                if 'block page_content' in source:
                    self.stdout.write("✓ Base has 'page_content' block")
                if 'block content' in source:
                    self.stdout.write("✓ Base has 'content' block")
                    
        except Exception as e:
            self.stdout.write(f"Error loading base template: {e}")
            import traceback
            traceback.print_exc()
        
        # Check base_site.html
        try:
            base_site_template = engine.get_template('admin/base_site.html')
            self.stdout.write(f"\nBase site template origin: {base_site_template.origin}")
            self.stdout.write(f"Base site template name: {base_site_template.template.name}")
            
            if hasattr(base_site_template, 'template'):
                source = base_site_template.template.source
                if 'block page_content' in source:
                    self.stdout.write("✓ Base site has 'page_content' block")
                if 'block content' in source:
                    self.stdout.write("✓ Base site has 'content' block")
                if 'block.super' in source:
                    self.stdout.write("✓ Base site uses block.super")
                    
        except Exception as e:
            self.stdout.write(f"Error loading base_site template: {e}")
            import traceback
            traceback.print_exc()
