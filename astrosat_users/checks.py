import functools
import operator
from itertools import chain

from django.conf import settings
from django.core.checks import register, Error, Tags

from . import APP_NAME
from .conf import app_settings


# apps required by astrosat_users
APP_DEPENDENCIES = [
    "astrosat",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "knox",
]


@register(Tags.compatibility)
def check_dependencies(app_configs, **kwargs):
    """
    Makes sure that all Django app dependencies are met.
    (Standard Python dependencies are handled in setup.py.)
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
def check_settings(app_configs):
    """
    Makes sure that some required settings are set as expected.
    """

    errors = []

    # obviously, a project that uses astrosat_users should use the astrosat_user User.
    user_model = settings.AUTH_USER_MODEL
    if user_model != f"{APP_NAME}.User":
        errors.append(
            Error(
                f"You are using {APP_NAME} which requires AUTH_USER_MODEL to be set to '{APP_NAME}.User'."
            )
        )

    # there can be multiple password validators defined;
    # they must include LengthPasswordValidator & StrongPasswordValidator
    password_validators = [
        validator["NAME"] for validator in settings.AUTH_PASSWORD_VALIDATORS
    ]
    if not all(
        validator in password_validators
        for validator in [
            "astrosat_users.validators.LengthPasswordValidator",
            "astrosat_users.validators.StrengthPasswordValidator",
        ]
    ):
        errors.append(
            Error(
                f"You are using {APP_NAME} which requires AUTH_PASSWORD_VALIDATORS to include LengthPasswordValidator & StrengthPasswordValidator"
            )
        )

    # there can be multiple template engines defined, which may-or-may-not set "OPTIONS" and/or "context_processors"
    # one of them must include "django.template.context_processors.request"
    template_context_processors = functools.reduce(
        operator.add,
        map(
            lambda x: x.get("OPTIONS", {}).get("context_processors", []),
            settings.TEMPLATES,
        ),
    )
    if "django.template.context_processors.request" not in template_context_processors:
        errors.append(
            Error(
                f"You are using {APP_NAME} which requires TEMPLATES to be set as per https://django-allauth.readthedocs.io/en/latest/installation.html"
            )
        )

    authentication_backends = settings.AUTHENTICATION_BACKENDS
    if (
        "allauth.account.auth_backends.AuthenticationBackend"
        not in authentication_backends
    ):
        errors.append(
            Error(
                f"You are using {APP_NAME} which requires AUTHENTICATION_BACKENDS to be set as per https://django-allauth.readthedocs.io/en/latest/installation.html"
            )
        )

    return errors


@register(Tags.compatibility)
def check_third_party_settings(app_configs):

    errors = []

    third_party_settings = [
        app_settings.ALLAUTH_SETTINGS,
        app_settings.REST_AUTH_SETTINGS,
    ]

    for key, value in chain(*map(lambda x: x.items(), third_party_settings)):
        setting = getattr(settings, key, None)
        if setting != value:
            errors.append(
                Error(
                    f"You are using {APP_NAME} which requires {key} to be set to {value}."
                )
            )
    return errors
