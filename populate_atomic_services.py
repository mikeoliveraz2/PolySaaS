#!/usr/bin/env python
"""
Script to populate AtomicService database records from existing service files.
This will create database entries for all valid atomic service files in dose/services/
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import AtomicService
from dose.services.atomic_services_registry import init_atomic_services_registry, ATOMIC_SERVICE_REGISTRY
import importlib.util
import inspect

def populate_atomic_services():
    """Populate AtomicService database records from existing files"""
    print("Initializing atomic services registry...")
    init_atomic_services_registry()

    print(f"Found {len(ATOMIC_SERVICE_REGISTRY)} atomic services in registry:")
    for name, cls in ATOMIC_SERVICE_REGISTRY.items():
        print(f"  - {name}: {cls}")

    services_dir = os.path.join(os.path.dirname(__file__), 'dose', 'services')
    created_count = 0
    updated_count = 0

    for service_name, service_class in ATOMIC_SERVICE_REGISTRY.items():
        try:
            # Get the module file path
            module = inspect.getmodule(service_class)
            if not module or not hasattr(module, '__file__'):
                print(f"  Warning: Could not find module file for {service_name}")
                continue

            module_file = module.__file__

            # Convert absolute path to relative path for FileField
            if module_file.startswith(services_dir):
                relative_path = os.path.relpath(module_file, services_dir)
                file_field_path = f'services/{relative_path}'
            else:
                print(f"  Warning: {service_name} file not in services directory: {module_file}")
                continue

            # Check if AtomicService record already exists
            atomic_service, created = AtomicService.objects.get_or_create(
                service_name=service_name,
                defaults={
                    'description': f'Auto-generated entry for {service_name} atomic service',
                    'config_json': {'name': 'value'},
                }
            )

            # Update the python_file field (careful not to trigger file operations)
            if created or not atomic_service.python_file:
                atomic_service.python_file.name = file_field_path
                atomic_service.save(update_fields=['python_file'])

            if created:
                created_count += 1
                print(f"  ✅ Created: {service_name}")
            else:
                updated_count += 1
                print(f"  📝 Updated: {service_name}")

        except Exception as e:
            print(f"  ❌ Error processing {service_name}: {e}")

    print(f"\nSummary:")
    print(f"  Created: {created_count} new AtomicService records")
    print(f"  Updated: {updated_count} existing AtomicService records")
    print(f"  Total AtomicService records: {AtomicService.objects.count()}")

    # List all AtomicService records
    print(f"\nAll AtomicService records in database:")
    for service in AtomicService.objects.all():
        print(f"  - {service.service_name}: {service.description}")

if __name__ == '__main__':
    populate_atomic_services()