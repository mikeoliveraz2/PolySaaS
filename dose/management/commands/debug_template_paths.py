from django.core.management.base import BaseCommand
from django.template import engines
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Debug template loading paths'

    def handle(self, *args, **options):
        self.stdout.write("=== Template Debug ===\n")
        
        # Show template dirs
        self.stdout.write("\nTemplate DIRS:")
        for engine in engines.all():
            for dir in engine.dirs:
                self.stdout.write(f"  {dir}")
                exists = "EXISTS" if os.path.isdir(dir) else "NOT FOUND"
                self.stdout.write(f"    -> {exists}")
        
        # Try to find the specific template
        self.stdout.write("\n\nSearching for admin/auth/user/change_form.html:")
        for engine in engines.all():
            try:
                template = engine.get_template('admin/auth/user/change_form.html')
                self.stdout.write(f"  Found: {template.template.name}")
                self.stdout.write(f"  Origin: {template.origin}")
            except Exception as e:
                self.stdout.write(f"  ERROR: {e}")
        
        # List files in BASE_DIR/templates/admin/auth/user/
        self.stdout.write(f"\n\nBASE_DIR: {settings.BASE_DIR}")
        test_path = os.path.join(settings.BASE_DIR, 'templates', 'admin', 'auth', 'user')
        self.stdout.write(f"\nChecking: {test_path}")
        if os.path.isdir(test_path):
            self.stdout.write("  Directory EXISTS")
            for f in os.listdir(test_path):
                self.stdout.write(f"    - {f}")
        else:
            self.stdout.write("  Directory NOT FOUND")
