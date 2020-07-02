from django.contrib import admin
from django.forms import ModelForm

from astrosat_users.models import Customer, CustomerUser


class CustomerUserAdminForm(ModelForm):
    class Meta:
        model = CustomerUser
        fields = "__all__"


class CustomerUserAdminInline(admin.TabularInline):
    model = CustomerUser
    form = CustomerUserAdminForm
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    inlines = (CustomerUserAdminInline,)
    list_display = ("name", "customer_type",)
    list_filter = ("customer_type",)
    search_fields = ("name", "title")
