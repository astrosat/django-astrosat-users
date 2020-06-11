from django.contrib import admin
from django.forms import ModelForm

from astrosat.admin import get_clickable_m2m_list_display

from astrosat_users.admin.admin_roles import update_roles_action
from astrosat_users.models import Customer, CustomerUser, UserRole


class CustomerUserAdminForm(ModelForm):
    class Meta:
        model = CustomerUser
        fields = "__all__"  # ["user", "owner", "access"]


class CustomerUserAdminInline(admin.TabularInline):
    model = CustomerUser
    form = CustomerUserAdminForm
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    actions = (update_roles_action,)
    inlines = (CustomerUserAdminInline,)
    filter_horizontal = ("roles",)
    list_display = ("name", "customer_type", "get_roles_for_list_display")
    list_filter = ("customer_type",)
    search_fields = ("name", "title")

    def get_queryset(self, request):
        # pre-fetching m2m fields that are used in list_displays
        # to avoid the "n+1" problem
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("roles")

    def get_roles_for_list_display(self, obj):
        return get_clickable_m2m_list_display(UserRole, obj.roles.all())

    get_roles_for_list_display.short_description = "roles"
