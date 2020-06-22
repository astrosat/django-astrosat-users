from astrosat.utils import DynamicAppSettings


# this is meant to be used just like Django's Project Settings:
# >>> from astrosat_users.conf import app_settings
# >>> app_settings.WHATEVER


app_settings = DynamicAppSettings("astrosat_users.conf.settings")
