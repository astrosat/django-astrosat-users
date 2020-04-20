from django import forms
from django.forms import ValidationError
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth import admin as auth_admin
from django.contrib.auth.models import Group, Permission
from django.http import HttpResponseRedirect
from django.shortcuts import render

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


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):

    actions = ("update_roles", "toggle_approval", "toggle_accepted_terms", "toggle_verication", "logout_all")

    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    fieldsets = (
        (
            "User",
            {
                "fields": (
                    "name",
                    "description",
                    "change_password",
                    "is_approved",
                    "accepted_terms",
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
        "accepted_terms",
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

    ###########
    # actions #
    ###########

    def toggle_approval(self, request, queryset):
        # TODO: doing this cleverly w/ negated F expressions is not supported (https://code.djangoproject.com/ticket/17186)
        # queryset.update(is_approved=not(F("is_approved")))
        for obj in queryset:
            obj.is_approved = not obj.is_approved
            obj.save()

            msg = f"{obj} {'not' if not obj.is_approved else ''} approved."
            self.message_user(request, msg)

    toggle_approval.short_description = "Toggles the approval of the selected users"

    def toggle_accepted_terms(self, request, queryset):
        # TODO: doing this cleverly w/ negated F expressions is not supported (https://code.djangoproject.com/ticket/17186)
        # queryset.update(accepted_terms=not(F("accepted_terms")))
        for obj in queryset:
            obj.accepted_terms = not obj.accepted_terms
            obj.save()

            msg = f"{obj} {'has not' if not obj.accepted_terms else 'has'} accepted terms."
            self.message_user(request, msg)

    toggle_approval.short_description = "Toggles the term acceptance of the selected users"

    def toggle_verication(self, request, queryset):

        for obj in queryset:

            emailaddress, created = obj.emailaddress_set.get_or_create(
                user=obj, email=obj.email
            )
            if not emailaddress.primary:
                emailaddress.set_as_primary(conditional=True)

            emailaddress.verified = not emailaddress.verified
            emailaddress.save()

            msg = f"{emailaddress} {'created and' if created else ''} {'not' if not emailaddress.verified else ''} verified."
            self.message_user(request, msg)

    toggle_verication.short_description = (
        "Toggles the verification of the selected users' primary email addresses"
    )

    def logout_all(self, request, queryset):
        for obj in queryset:
            obj.logout_all()

            msg = f"logged {obj} out of all sessions."
            self.message_user(request, msg)

    logout_all.short_description = "Logs the selected users out of all active sessions"

    def update_roles(self, request, queryset):
        class _UpdateRolesForm(forms.Form):
            _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
            included_roles = forms.ModelMultipleChoiceField(
                required=False, label="Included Roles", queryset=UserRole.objects.all(),
            )
            excluded_roles = forms.ModelMultipleChoiceField(
                required=False, label="Excluded Roles", queryset=UserRole.objects.all()
            )

            def clean(self):
                cleaned_data = super().clean()
                included_roles = cleaned_data["included_roles"]
                excluded_roles = cleaned_data["excluded_roles"]
                if included_roles.intersection(excluded_roles).exists():
                    raise ValidationError(
                        "Included and excluded roles must be mutually-exclusive."
                    )

        update_roles_form = _UpdateRolesForm(
            request.POST or None,
            initial={
                "_selected_action": request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
            },
        )

        if "apply" in request.POST:
            if update_roles_form.is_valid():
                included_roles = update_roles_form.cleaned_data["included_roles"]
                excluded_roles = update_roles_form.cleaned_data["excluded_roles"]

                for obj in queryset:

                    existing_roles = obj.roles.all()
                    roles_to_add = included_roles.difference(existing_roles)
                    roles_to_remove = excluded_roles.intersection(existing_roles)
                    obj.roles.add(*roles_to_add)
                    obj.roles.remove(*roles_to_remove)

                    if roles_to_add.exists() or roles_to_remove.exists():
                        msg = f"Successfully added '{', '.join([r.name for r in roles_to_add])}' and removed '{', '.join([r.name for r in roles_to_remove])}' from '{obj}'."
                        self.message_user(request, msg)

                return HttpResponseRedirect(request.get_full_path())

        context = {
            "form": update_roles_form,
            "users": get_clickable_m2m_list_display(User, queryset),
            "site_header": getattr(settings, "ADMIN_SITE_HEADER", None),
            "site_title": getattr(settings, "ADMIN_SITE_TITLE", None),
            "index_title": getattr(settings, "ADMIN_INDEX_TITLE", None),
        }
        return render(
            request, "astrosat_users/admin/update_roles.html", context=context
        )

    update_roles.short_description = (
        "Updates the selected users to include/exclude roles"
    )
