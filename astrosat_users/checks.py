import functools
import operator

from django.conf import settings
from django.core.checks import register, Error, Tags

from . import APP_NAME


# apps required by astrosat
APP_DEPENDENCIES = [
    'astrosat',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'rest_auth',
    'rest_framework.authtoken',   # required for rest_auth !

]


@register(Tags.compatibility)
def check_dependencies(app_configs, **kwargs):
    """
    Makes sure that all django app dependencies are met.
    (Standard python dependencies are handled in setup.py.)
    Called by `AppConfig.ready()`.
    """

    errors = []
    for i, dependency in enumerate(APP_DEPENDENCIES):
        if dependency not in settings.INSTALLED_APPS:
            errors.append(
                Error(
                    f"You are using {APP_NAME} which requires the {dependency} module.  Please install it and add it to INSTALLED_APPS.",
                    id=f"{APP_NAME}:E{i:03}",
                )
            )

    return errors


@register(Tags.compatibility)
def check_allauth_settings(app_configs):

    errors = []

    user_model = settings.AUTH_USER_MODEL
    if user_model != f"{APP_NAME}.User":
        errors.append(
            Error(
                f"You are using {APP_NAME} which requires AUTH_USER_MODEL to be set to '{APP_NAME}.User'."
            )
        )

    account_adapter = getattr(settings, "ACCOUNT_ADAPTER", None)
    socialaccount_adapter = getattr(settings, "SOCIALACCOUNT_ADAPTER", None)
    if account_adapter != f"{APP_NAME}.adapters.AccountAdapter" or socialaccount_adapter != f"{APP_NAME}.adapters.SocialAccountAdapter":
        errors.append(
            Error(
                f"You are using {APP_NAME} which requires specifying appropriate account_adapters in settings.py"
            )
        )

    # there can be multiple template engines defined, which may-or-may-not set "OPTIONS" and/or "context_processors"
    # one of them must include "django.template.context_processors.request"
    template_context_processors = functools.reduce(operator.add, map(lambda x: x.get("OPTIONS", {}).get("context_processors", []), settings.TEMPLATES))
    if "django.template.context_processors.request" not in template_context_processors:
        errors.append(
            Error(
                f"You are using {APP_NAME} which requires TEMPLATES to be set as per https://django-allauth.readthedocs.io/en/latest/installation.html",
            )
        )

    authentication_backends = settings.AUTHENTICATION_BACKENDS
    if "allauth.account.auth_backends.AuthenticationBackend" not in authentication_backends:
        errors.append(
            Error(
                f"You are using {APP_NAME} which requires AUTHENTICATION_BACKENDS to be set as per https://django-allauth.readthedocs.io/en/latest/installation.html",
            )
        )

    return errors


@register(Tags.compatibility)
def check_rest_auth_settings(app_configs):

    errors = []

    rest_auth_serializers = getattr(settings, "REST_AUTH_SERIALIZERS", None)
    if not isinstance(rest_auth_serializers, dict):
        errors.append(
            Error(
                f"You are using {APP_NAME} which requires you to set REST_AUTH_SETTINGS."
            )
        )

    PASSWORD_RESET_SERIALIZER = f"{APP_NAME}.serializers.PasswordResetSerializer"
    if rest_auth_serializers.get("PASSWORD_RESET_SERIALIZER") != PASSWORD_RESET_SERIALIZER:
        errors.append(
            Error(
                f"You are using {APP_NAME} which requirs you to set REST_AUTH_SETTINGS[PASSWORD_RESET_SERIALIZER] to '{PASSWORD_RESET_SERIALIZER}'."
            )
        )
    PASSWORD_RESET_CONFIRM_SERIALIZER = f"{APP_NAME}.serializers.PasswordResetConfirmSerializer"
    if rest_auth_serializers.get("PASSWORD_RESET_CONFIRM_SERIALIZER") != PASSWORD_RESET_CONFIRM_SERIALIZER:
        errors.append(
            Error(
                f"You are using {APP_NAME} which requirs you to set REST_AUTH_SETTINGS[PASSWORD_RESET_CONFIRM_SERIALIZER] to '{PASSWORD_RESET_CONFIRM_SERIALIZER}'."
            )
        )


    return errors
