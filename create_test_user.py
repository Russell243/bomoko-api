from django.contrib.auth import get_user_model
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bomoko.settings.dev')
django.setup()

User = get_user_model()
username = '0800000000'
password = 'Bomoko2024'

u, created = User.objects.get_or_create(username=username, defaults={'phone_number': username})
u.set_password(password)
u.is_active = True
u.is_staff = True
u.is_superuser = True
u.save()

print(f"User {username} {'created' if created else 'updated'} with password {password}")
