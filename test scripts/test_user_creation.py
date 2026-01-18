#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.admin.models import LogEntry

def test_user_creation():
    """Test if we can create a user and admin log entry without constraint errors."""
    try:
        print("Testing user creation...")
        
        # Check if test user already exists
        if User.objects.filter(username='testuser123').exists():
            print("Test user already exists, deleting...")
            User.objects.filter(username='testuser123').delete()
        
        # Create a test user
        user = User.objects.create_user(
            username='testuser123',
            email='test@example.com',
            password='testpassword123'
        )
        print(f"✅ Successfully created user: {user.username} (ID: {user.id})")
        
        # Test creating an admin log entry (this would trigger the constraint)
        log_entry = LogEntry.objects.create(
            user=user,
            content_type_id=1,  # Content type for User model typically
            object_id=user.id,
            object_repr=str(user),
            action_flag=1,  # ADDITION
            change_message="Test log entry"
        )
        print(f"✅ Successfully created admin log entry: {log_entry.id}")
        
        # Clean up test data
        log_entry.delete()
        user.delete()
        print("✅ Test completed successfully - constraint issue appears to be resolved!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_user_creation()
