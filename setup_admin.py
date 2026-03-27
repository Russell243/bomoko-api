import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bomoko.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Profile

User = get_user_model()

username = "master_admin"
email = "admin@bomoko.app"
password = "BomokoAdmin2026!"

if not User.objects.filter(username=username).exists():
    user = User.objects.create_superuser(username=username, email=email, password=password)
    
    # Ensure profile role is admin
    if hasattr(user, 'profile'):
        user.profile.role = 'admin'
        user.profile.save()
    else:
        Profile.objects.create(user=user, role='admin')
        
    print(f"SUCCESS: Superuser '{username}' created with password '{password}'")
else:
    print(f"INFO: Superuser '{username}' already exists.")
