from django.contrib import admin
from django.contrib.auth import admin as auth_admin

from django.contrib.auth.models import Group, Permission

from astrosat_users.forms import UserAdminChangeForm, UserAdminCreationForm
from astrosat_users.models import User, UserSettings, UserRole, UserPermission


# don't let the built-in Django Roles system
# get in-the-way-of the astrosat_users roles
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass
try:
    admin.site.unregister(Permission)
except admin.sites.NotRegistered:
    pass


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    pass


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    pass


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    filter_horizontal = ("permissions",)


def logout_all(model_admin, request, queryset):
    for obj in queryset:
        obj.logout_all()


logout_all.short_description = "Logs the selected users out of all active sessions"


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):

    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    actions = (logout_all,)
    fieldsets = (
        (
            "User",
            {
                "fields": (
                    "name",
                    "description",
                    "change_password",
                    "is_approved",
                    "roles",
                )
            },
        ),
    ) + auth_admin.UserAdmin.fieldsets
    list_display = [
        "username",
        "name",
        "is_superuser",
        "is_verified_pretty",
        "is_approved",
        "is_active",
    ]
    search_fields = ["username", "name", "email"]

    filter_horizontal = (
        "roles",
    )  # makes a pretty widget; the same one as used by "groups"

    def is_verified_pretty(self, instance):
        # makes the "is_verified" property look pretty in list_display
        return instance.is_verified

    is_verified_pretty.boolean = True
    is_verified_pretty.short_description = "IS VERIFIED"
