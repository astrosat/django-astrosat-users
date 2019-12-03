from django.apps import AppConfig

from . import APP_NAME


class ExampleAppConfig(AppConfig):

    name = APP_NAME

    def ready(self):

        try:
            # register any checks...
            import example.checks  # noqa
        except ImportError:
            pass

        try:
            # register any signals...
            import example.signals  # noqa
        except ImportError:
            pass
