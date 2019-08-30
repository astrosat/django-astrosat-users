from django.contrib import admin

from astrosat.admin import CannotAddModelAdminBase

from .models import ExampleProfile


@admin.register(ExampleProfile)
class UserProfileAdmin(CannotAddModelAdminBase, admin.ModelAdmin):
    pass
