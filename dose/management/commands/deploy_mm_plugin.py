from django.core.management.base import BaseCommand
import requests
import os
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Deploy Mattermost passthrough plugin to Mattermost server'

    def handle(self, *args, **options):
        from django.conf import settings
        
        mm_url = getattr(settings, 'MATTERMOST_SHARED_URL', 'https://polysaas-mattermost.onrender.com')
        plugin_path = 'f:\\PolySaaS\\mattermost-passthrough-plugin\\polysaas-passthrough-plugin.zip'
        
        # mmadmin credentials
        admin_username = 'mmadmin'
        admin_password = 'PolySaaS2026!'
        
        self.stdout.write(f'Working with Mattermost: {mm_url}')
        self.stdout.write(f'Plugin path: {plugin_path}')
        
        # Check if plugin file exists
        if not os.path.exists(plugin_path):
            self.stdout.write(self.style.ERROR(f'Plugin file not found: {plugin_path}'))
            return
        
        # Login as mmadmin to get token
        self.stdout.write(f'Logging in as {admin_username}...')
        try:
            login_resp = requests.post(
                f"{mm_url}/api/v4/users/login",
                json={'login_id': admin_username, 'password': admin_password},
                timeout=30,
            )
            if login_resp.status_code != 200:
                self.stdout.write(self.style.ERROR(f'Login failed: {login_resp.status_code} - {login_resp.text[:200]}'))
                return
            
            token = login_resp.headers.get('Token')
            if not token:
                self.stdout.write(self.style.ERROR('No token in login response'))
                return
            
            headers = {"Authorization": f"Bearer {token}"}
            self.stdout.write(self.style.SUCCESS('Login successful'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Login exception: {e}'))
            return
        
        # Upload plugin
        self.stdout.write('Uploading plugin...')
        try:
            with open(plugin_path, 'rb') as f:
                upload_resp = requests.post(
                    f"{mm_url}/api/v4/plugins",
                    headers=headers,
                    files={'plugin': ('polysaas-passthrough-plugin.zip', f, 'application/zip')},
                    timeout=60,
                )
            
            if upload_resp.status_code == 201:
                plugin_id = upload_resp.json().get('id')
                self.stdout.write(self.style.SUCCESS(f'Plugin uploaded (id={plugin_id})'))
            elif upload_resp.status_code == 409:
                self.stdout.write(self.style.WARNING('Plugin already installed, updating...'))
                # Need to get existing plugin ID and update
                self._update_existing_plugin(mm_url, headers, plugin_path)
                return
            else:
                self.stdout.write(self.style.ERROR(f'Upload failed: {upload_resp.status_code} - {upload_resp.text[:200]}'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Upload exception: {e}'))
            return
        
        # Enable plugin
        self.stdout.write('Enabling plugin...')
        try:
            enable_resp = requests.post(
                f"{mm_url}/api/v4/plugins/{plugin_id}/enable",
                headers=headers,
                timeout=30,
            )
            if enable_resp.status_code == 200:
                self.stdout.write(self.style.SUCCESS('Plugin enabled successfully'))
            else:
                self.stdout.write(self.style.WARNING(f'Enable failed: {enable_resp.status_code} - {enable_resp.text[:200]}'))
                self.stdout.write('You may need to enable it manually in System Console')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Enable exception: {e}'))
            self.stdout.write('You may need to enable it manually in System Console')
        
        self.stdout.write(self.style.SUCCESS('Plugin deployment complete'))
    
    def _update_existing_plugin(self, mm_url: str, headers: dict, plugin_path: str):
        """Update existing plugin installation."""
        try:
            # Get list of plugins to find our plugin
            list_resp = requests.get(f"{mm_url}/api/v4/plugins", headers=headers, timeout=30)
            if list_resp.status_code != 200:
                self.stdout.write(self.style.ERROR(f'Failed to list plugins: {list_resp.status_code}'))
                return
            
            plugins = list_resp.json()
            plugin_id = None
            for plugin in plugins:
                if plugin.get('id') == 'com.polysaas.passthrough':
                    plugin_id = plugin.get('id')
                    break
            
            if not plugin_id:
                self.stdout.write(self.style.ERROR('Plugin not found in installed list'))
                return
            
            # Remove existing plugin
            self.stdout.write(f'Removing existing plugin {plugin_id}...')
            remove_resp = requests.delete(f"{mm_url}/api/v4/plugins/{plugin_id}", headers=headers, timeout=30)
            if remove_resp.status_code == 200:
                self.stdout.write(self.style.SUCCESS('Existing plugin removed'))
            else:
                self.stdout.write(self.style.WARNING(f'Remove failed: {remove_resp.status_code}'))
            
            # Upload new version
            self.stdout.write('Uploading new version...')
            with open(plugin_path, 'rb') as f:
                upload_resp = requests.post(
                    f"{mm_url}/api/v4/plugins",
                    headers=headers,
                    files={'plugin': ('polysaas-passthrough-plugin.zip', f, 'application/zip')},
                    timeout=60,
                )
            
            if upload_resp.status_code == 201:
                self.stdout.write(self.style.SUCCESS('New plugin uploaded'))
            else:
                self.stdout.write(self.style.ERROR(f'Upload failed: {upload_resp.status_code} - {upload_resp.text[:200]}'))
                return
            
            # Enable plugin
            self.stdout.write('Enabling plugin...')
            enable_resp = requests.post(
                f"{mm_url}/api/v4/plugins/{plugin_id}/enable",
                headers=headers,
                timeout=30,
            )
            if enable_resp.status_code == 200:
                self.stdout.write(self.style.SUCCESS('Plugin enabled successfully'))
            else:
                self.stdout.write(self.style.WARNING(f'Enable failed: {enable_resp.status_code}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Update exception: {e}'))
