from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.models import Group, Permission
from django.http import HttpResponseRedirect
from django.shortcuts import render

from astrosat_users.models import UserPermission, UserRole

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

#################
# admin classes #
#################


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    pass


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    filter_horizontal = ("permissions", )


#################
# admin actions #
#################


def update_roles_action(modeladmin, request, queryset):
    """
    used by UserAdmin & CustomerAdmin to update roles in bulk
    """
    class UpdateRolesForm(forms.Form):
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
        included_roles = forms.ModelMultipleChoiceField(
            required=False,
            label="Included Roles",
            queryset=UserRole.objects.all()
        )
        excluded_roles = forms.ModelMultipleChoiceField(
            required=False,
            label="Excluded Roles",
            queryset=UserRole.objects.all()
        )

        def clean(self):
            cleaned_data = super().clean()
            included_roles = cleaned_data["included_roles"]
            excluded_roles = cleaned_data["excluded_roles"]
            if included_roles.intersection(excluded_roles).exists():
                raise forms.ValidationError(
                    "Included and excluded roles must be mutually-exclusive."
                )

    update_roles_form = UpdateRolesForm(
        request.POST or None,
        initial={
            "_selected_action":
                request.POST.getlist(admin.helpers.ACTION_CHECKBOX_NAME)
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
                    modeladmin.message_user(request, msg)

            return HttpResponseRedirect(request.get_full_path())

    context = {
        "site_header": getattr(settings, "ADMIN_SITE_HEADER", None),
        "site_title": getattr(settings, "ADMIN_SITE_TITLE", None),
        "index_title": getattr(settings, "ADMIN_INDEX_TITLE", None),
        "opts": modeladmin.model._meta,
        "form": update_roles_form,
        "objects": queryset,
    }
    return render(
        request, "astrosat_users/admin/update_roles.html", context=context
    )


update_roles_action.short_description = (
    "Updates the selected objects to include/exclude roles"
)
