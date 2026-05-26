from django.core.management.base import BaseCommand
import requests
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Add mmadmin system admin user to existing Mattermost instance'

    def handle(self, *args, **options):
        from django.conf import settings
        
        mm_url = getattr(settings, 'MATTERMOST_SHARED_URL', 'https://polysaas-mattermost.onrender.com')
        admin_token = getattr(settings, 'MATTERMOST_ADMIN_TOKEN', '')
        
        if not admin_token:
            self.stdout.write(self.style.ERROR('MATTERMOST_ADMIN_TOKEN not configured in settings'))
            return
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # mmadmin credentials
        admin_username = 'mmadmin'
        admin_password = 'PolySaaS2026!'
        admin_email = f'{admin_username}@polysaas.local'
        
        self.stdout.write(f'Working with Mattermost: {mm_url}')
        
        # Check if user already exists
        try:
            resp = requests.get(f"{mm_url}/api/v4/users/username/{admin_username}", headers=headers, timeout=10)
            if resp.status_code == 200:
                user = resp.json()
                self.stdout.write(self.style.WARNING(f'User {admin_username} already exists (id={user["id"]})'))
                # Ensure system admin role
                self._promote_to_system_admin(mm_url, headers, user['id'])
                # Ensure dev team exists and add user
                dev_team_id = self._ensure_dev_team(mm_url, headers)
                if dev_team_id:
                    self._add_user_to_team(mm_url, headers, dev_team_id, user['id'])
                return
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Error checking for user: {e}'))
        
        # Create the user
        try:
            resp = requests.post(
                f"{mm_url}/api/v4/users",
                headers=headers,
                json={
                    'email': admin_email,
                    'username': admin_username,
                    'password': admin_password,
                    'first_name': 'PolySaaS',
                    'last_name': 'Admin'
                },
                timeout=30,
            )
            if resp.status_code == 201:
                user = resp.json()
                self.stdout.write(self.style.SUCCESS(f'Created user {admin_username} (id={user["id"]})'))
                # Promote to system admin
                self._promote_to_system_admin(mm_url, headers, user['id'])
                # Ensure dev team exists and add user
                dev_team_id = self._ensure_dev_team(mm_url, headers)
                if dev_team_id:
                    self._add_user_to_team(mm_url, headers, dev_team_id, user['id'])
                self.stdout.write(self.style.SUCCESS('mmadmin setup complete'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to create user: {resp.status_code} - {resp.text[:200]}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Exception creating user: {e}'))
    
    def _promote_to_system_admin(self, mm_url: str, headers: dict, user_id: str):
        """Promote user to system admin role."""
        try:
            resp = requests.get(f"{mm_url}/api/v4/users/{user_id}", headers=headers, timeout=10)
            if resp.status_code != 200:
                self.stdout.write(self.style.ERROR(f'Failed to get user: {resp.text[:200]}'))
                return
            
            user = resp.json()
            current_roles = user.get('roles', '')
            
            if 'system_admin' not in current_roles:
                new_roles = current_roles + ' system_admin' if current_roles else 'system_admin'
                patch_resp = requests.put(
                    f"{mm_url}/api/v4/users/{user_id}/roles",
                    headers=headers,
                    json={'roles': new_roles},
                    timeout=30,
                )
                if patch_resp.status_code == 200:
                    self.stdout.write(self.style.SUCCESS(f'Promoted {user_id} to system admin'))
                else:
                    self.stdout.write(self.style.ERROR(f'Failed to promote: {patch_resp.text[:200]}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'User already has system admin role'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Exception promoting user: {e}'))
    
    def _ensure_dev_team(self, mm_url: str, headers: dict) -> str:
        """Ensure PolySaaS Dev Team exists, return team ID."""
        team_name = 'PolySaaS Dev Team'
        team_slug = team_name.replace(' ', '-')
        
        try:
            resp = requests.get(f"{mm_url}/api/v4/teams/name/{team_slug}", headers=headers, timeout=10)
            if resp.status_code == 200:
                team = resp.json()
                self.stdout.write(self.style.SUCCESS(f'Dev team already exists (id={team["id"]})'))
                return team['id']
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Error checking for dev team: {e}'))
        
        # Create the team
        try:
            resp = requests.post(
                f"{mm_url}/api/v4/teams",
                headers=headers,
                json={
                    'name': team_slug,
                    'display_name': team_name,
                    'type': 'O'
                },
                timeout=30,
            )
            if resp.status_code == 201:
                team = resp.json()
                self.stdout.write(self.style.SUCCESS(f'Created dev team (id={team["id"]})'))
                return team['id']
            else:
                self.stdout.write(self.style.ERROR(f'Failed to create dev team: {resp.text[:200]}'))
                return None
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Exception creating dev team: {e}'))
            return None
    
    def _add_user_to_team(self, mm_url: str, headers: dict, team_id: str, user_id: str):
        """Add user to team."""
        try:
            resp = requests.post(
                f"{mm_url}/api/v4/teams/{team_id}/members",
                headers=headers,
                json={'user_id': user_id},
                timeout=30,
            )
            if resp.status_code == 201:
                self.stdout.write(self.style.SUCCESS(f'Added user to team'))
            elif resp.status_code == 400 and 'already' in resp.text.lower():
                self.stdout.write(self.style.SUCCESS(f'User already in team'))
            else:
                self.stdout.write(self.style.WARNING(f'Failed to add to team: {resp.status_code} - {resp.text[:100]}'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Exception adding to team: {e}'))
