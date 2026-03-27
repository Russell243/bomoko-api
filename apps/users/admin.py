from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profil Étendu'
    fk_name = 'user'

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline, )
    list_display = ('username', 'phone_number', 'email', 'get_role', 'is_verified', 'is_staff')
    list_select_related = ('profile', )
    
    def get_role(self, instance):
        return instance.profile.get_role_display()
    get_role.short_description = 'Rôle Utilisateur'

