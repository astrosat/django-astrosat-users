from django.contrib import admin
from django.contrib.auth import admin as auth_admin

from django.contrib.auth.models import Group, Permission

from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import User, UserSettings


try:
    admin.site.register(Group)
except admin.sites.AlreadyRegistered:
    pass
try:
    admin.site.register(Permission)
except admin.sites.AlreadyRegistered:
    pass


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    pass


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):

    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    fieldsets = (
        (
            "User", {
                "fields": (
                    "name",
                    "description",
                    "change_password",
                    "is_approved",
                )
            }
        ),
    ) + auth_admin.UserAdmin.fieldsets
    list_display = ["username", "name", "is_superuser", "is_verified", "is_approved", "is_active"]
    search_fields = ["username", "name", "email"]