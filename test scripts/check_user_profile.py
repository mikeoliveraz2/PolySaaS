from django.contrib.auth.models import User
from dose.models import UserProfile

try:
    u = User.objects.get(id=7)
    print(f'User: {u.username}')
    print(f'Has userprofile attr: {hasattr(u, "userprofile")}')

    profiles = UserProfile.objects.filter(user_id=7)
    print(f'Profile count in DB: {profiles.count()}')

    for i, p in enumerate(profiles):
        print(f'  Profile {i+1}: id={p.id}, tenant={p.tenant.name if p.tenant else "None"}')

except User.DoesNotExist:
    print('User 7 does not exist')
except Exception as e:
    print(f'Error: {e}')
