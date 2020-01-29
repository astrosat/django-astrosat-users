from django.contrib import admin, messages
from django.contrib.auth import admin as auth_admin

from django.contrib.auth.models import Group, Permission

from astrosat.admin import get_clickable_m2m_list_display

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


def toggle_approval(model_admin, request, queryset):
    # TODO: doing this cleverly w/ negated F expressions is not supported (https://code.djangoproject.com/ticket/17186)
    # queryset.update(is_approved=not(F("is_approved")))
    for obj in queryset:
        obj.is_approved = not obj.is_approved
        obj.save()

        msg = f"{obj} {'not' if not obj.is_approved else ''} approved."
        messages.add_message(request, messages.INFO, msg)


toggle_approval.short_description = "Toggles the approval of the selected users"


def toggle_verication(model_admin, request, queryset):

    for obj in queryset:

        emailaddress, created = obj.emailaddress_set.get_or_create(
            user=obj, email=obj.email
        )
        if not emailaddress.primary:
            emailaddress.set_as_primary(conditional=True)

        emailaddress.verified = not emailaddress.verified
        emailaddress.save()

        msg = f"{emailaddress} {'created and' if created else ''} {'not' if not emailaddress.verified else ''} verified."
        messages.add_message(request, messages.INFO, msg)


toggle_verication.short_description = (
    "Toggles the verification of the selected users' primary email addresses"
)


def logout_all(model_admin, request, queryset):
    for obj in queryset:
        obj.logout_all()

        msg = f"logged {obj} out of all sessions."
        messages.add_message(request, messages.INFO, msg)


logout_all.short_description = "Logs the selected users out of all active sessions"


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):

    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    actions = (toggle_approval, toggle_verication, logout_all)
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
        "email",
        "name",
        "get_roles_for_list_display",
        "is_superuser",
        "is_verified_pretty",
        "is_approved",
        "is_active",
    ]
    list_filter = auth_admin.UserAdmin.list_filter + ("roles",)

    search_fields = ["username", "name", "email"]

    filter_horizontal = (
        "roles",
    )  # makes a pretty widget; the same one as used by "groups"

    def get_roles_for_list_display(self, obj):
        return get_clickable_m2m_list_display(UserRole, obj.roles.all())

    get_roles_for_list_display.short_description = "roles"

    def is_verified_pretty(self, instance):
        # makes the "is_verified" property look pretty in list_display
        return instance.is_verified

    is_verified_pretty.boolean = True
    is_verified_pretty.short_description = "IS VERIFIED"
