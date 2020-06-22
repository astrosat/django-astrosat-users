from django.contrib import admin

from astrosat_users.models import UserSettings


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    pass
