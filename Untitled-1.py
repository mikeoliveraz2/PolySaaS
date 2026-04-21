# Run via: railway run python manage.py shell
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.get(username='olientAdmin')
u.set_password('PolySaas2026!')
u.save()