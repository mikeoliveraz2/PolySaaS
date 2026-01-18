quit()
from django.contrib.auth.models import User
from dose.models import Tenant, UserProfile

# Change these values as needed
username = 'normaluser'
password = 'testpassword123'
email = 'normaluser@example.com'
tenant_schema = 'public'  # or another schema_name for a different tenant

# Get or create the tenant
tenant = Tenant.objects.filter(schema_name=tenant_schema).first()
if not tenant:
    print(f"Tenant with schema_name '{tenant_schema}' does not exist.")
else:
    # Create the user
    user, created = User.objects.get_or_create(username=username, defaults={
        'email': email,
        'is_active': True,
        'is_staff': False,
        'is_superuser': False,
    })
    if created:
        user.set_password(password)
        user.save()
        print(f"User '{username}' created.")
    else:
        print(f"User '{username}' already exists.")
    # Ensure UserProfile exists and is assigned to tenant
    try:
        profile = UserProfile.objects.get(user=user)
        if profile.tenant != tenant:
            profile.tenant = tenant
            profile.save()
            print(f"UserProfile for '{username}' updated to tenant '{tenant.name}'.")
        else:
            print(f"UserProfile for '{username}' already exists and assigned to tenant '{tenant.name}'.")
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user, tenant=tenant)
        print(f"UserProfile for '{username}' created and assigned to tenant '{tenant.name}'.")
    print(f"Username: {username}\nPassword: {password}\nTenant: {tenant.name}")
