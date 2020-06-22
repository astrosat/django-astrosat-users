from django.contrib import admin, messages
from django.contrib.auth import admin as auth_admin

from astrosat.admin import get_clickable_m2m_list_display

from astrosat_users.admin.admin_roles import update_roles_action
from astrosat_users.forms import UserAdminChangeForm, UserAdminCreationForm
from astrosat_users.models import User, Customer, UserRole


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):

    actions = (
        "toggle_approval",
        "toggle_accepted_terms",
        "toggle_verication",
        "logout_all",
    ) + (update_roles_action,)
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    fieldsets = (
        (
            "User",
            {
                "fields": (
                    "avatar",
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
        "is_superuser",
        "is_verified_for_list_display",
        "is_approved",
        "is_active",
        "accepted_terms",
        "get_roles_for_list_display",
        "get_customers_for_list_display",
    ]
    list_filter = auth_admin.UserAdmin.list_filter + ("customers",)
    search_fields = ["username", "name", "email"]
    filter_horizontal = (
        "roles",
    )  # makes a pretty widget; the same one as used by "groups"

    def get_queryset(self, request):
        # pre-fetching m2m fields that are used in list_displays
        # to avoid the "n+1" problem
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("roles", "customers")

    def is_verified_for_list_display(self, instance):
        # makes the "is_verified" property look pretty in list_display
        return instance.is_verified

    is_verified_for_list_display.boolean = True
    is_verified_for_list_display.short_description = "IS VERIFIED"

    def get_customers_for_list_display(self, obj):
        return get_clickable_m2m_list_display(Customer, obj.customers.all())

    get_customers_for_list_display.short_description = "customers"

    def get_roles_for_list_display(self, obj):
        return get_clickable_m2m_list_display(UserRole, obj.roles.all())

    get_roles_for_list_display.short_description = "roles"

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

    toggle_accepted_terms.short_description = (
        "Toggles the term acceptance of the selected users"
    )

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
