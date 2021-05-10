from django.apps import AppConfig

from . import APP_NAME


class AstrosatUsersConfig(AppConfig):

    name = APP_NAME
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):

        try:
            # register any checks...
            import astrosat_users.checks  # noqa
        except ImportError:
            pass

        try:
            # register any signals...
            import astrosat_users.signals  # noqa
        except ImportError:
            pass
