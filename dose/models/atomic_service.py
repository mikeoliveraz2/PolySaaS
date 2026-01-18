import os
import shutil
import importlib.util
import sys
from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

class AtomicService(models.Model):
    service_name = models.CharField(max_length=100, unique=True, help_text="Service name (used for registration and lookup)")
    python_file = models.FileField(
        upload_to='services/',
        validators=[FileExtensionValidator(['py'])],
        help_text="Python file implementing the atomic service. Must extend AtomicServiceBase."
    )
    description = models.TextField(blank=True, help_text="Description of the atomic service")
    def default_config_json():
        return {'name': 'value'}
    config_json = models.JSONField(
        blank=True,
        null=True,
        default=default_config_json,
        help_text="JSON parameters for service configuration. Default: {'name': 'value'}"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.service_name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.python_file:
            # Get the correct services directory: dose/services/ not dose/models/services/
            dose_dir = os.path.dirname(os.path.dirname(__file__))  # Go up from dose/models/ to dose/
            dest_dir = os.path.join(dose_dir, 'services')
            dest_path = os.path.join(dest_dir, os.path.basename(self.python_file.name))
            src_path = self.python_file.path
            if not os.path.abspath(src_path).startswith(os.path.abspath(dest_dir)):
                # Check if source file exists before trying to copy
                if os.path.exists(src_path):
                    shutil.copy2(src_path, dest_path)
                    self.python_file.name = f'services/{os.path.basename(self.python_file.name)}'
                    super().save(update_fields=['python_file'])
                else:
                    # File doesn't exist - this is okay for auto-generated entries
                    # The file already exists in the services directory
                    print(f"[AtomicService] Source file {src_path} not found - assuming file is already in services directory")
            try:
                spec = importlib.util.spec_from_file_location(self.service_name, dest_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[self.service_name] = module
                spec.loader.exec_module(module)
                found = False
                from dose.services.atomic_service_base import AtomicServiceBase
                for attr in dir(module):
                    obj = getattr(module, attr)
                    if isinstance(obj, type) and issubclass(obj, AtomicServiceBase) and obj is not AtomicServiceBase:
                        found = True
                        break
                if not found:
                    raise ValidationError(f"Uploaded file does not define a class extending AtomicServiceBase.")
            except Exception as e:
                raise ValidationError(f"AtomicService verification failed: {e}")
            try:
                from dose.services.atomic_services_registry import init_atomic_services_registry
                init_atomic_services_registry()
            except Exception as e:
                print(f"Registry update failed: {e}")
    class Meta:
        verbose_name = "Atomic Service"
        verbose_name_plural = "Atomic Services"
