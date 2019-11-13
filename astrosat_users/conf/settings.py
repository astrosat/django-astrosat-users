import environ

from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from astrosat.utils import DynamicSetting


env = environ.Env()


PROJECT_NAME = "Django Astrosat Users"
PROJECT_SLUG = slugify(PROJECT_NAME)
PROJECT_EMAIL = "{role}@astrosat.space"

LOGIN_REDIRECT_URL = getattr(settings, "LOGIN_REDIRECT_URL", "/")
LOGOUT_REDIRECT_URL = getattr(settings, "LOGOUT_REDIRECT_URL", "/")
VERIFICATION_REDIRECT_URL = getattr(settings, "VERIFICATION_REDIRECT_URL", "/")
APPROVAL_REDIRECT_URL = getattr(settings, "APPROVAL_REDIRECT_URL", "/")

ASTROSAT_USERS_REQUIRE_VERIFICATION = getattr(
    settings,
    "ASTROSAT_USERS_REQUIRE_VERIFICATION",
    DynamicSetting(
        "astrosat_users.UserSettings.require_verification",
        env("DJANGO_ASTROSAT_USERS_REQUIRE_VERIFICATION", default=True),
    ),
)

ASTROSAT_USERS_REQUIRE_APPROVAL = getattr(
    settings,
    "ASTROSAT_USERS_REQUIRE_APPROVAL",
    DynamicSetting(
        "astrosat_users.UserSettings.require_approval",
        env("DJANGO_ASTROSAT_USERS_REQUIRE_APPROVAL", default=False),
    ),
)

ASTROSAT_USERS_ALLOW_REGISTRATION = getattr(
    settings,
    "ASTROSAT_USERS_ALLOW_REGISTRATION",
    DynamicSetting(
        "astrosat_users.UserSettings.allow_registration",
        env("DJANGO_ASTROSAT_USERS_ALLOW_REGISTRATION", default=True),
    ),
)

ASTROSAT_USERS_ENABLE_BACKEND_ACCESS = getattr(
    settings,
    "ASTROSAT_USERS_ENABLE_BACKEND_ACCESS",
    DynamicSetting(
        "astrosat_users.UserSettings.enable_backend_access",
        env("DJANGO_ASTROSAT_USERS_ENABLE_BACKEND_ACCESS", default=True),
    ),
)

ASTROSAT_USERS_NOTIFY_SIGNUPS = getattr(
    settings,
    "ASTROSAT_USERS_NOTIFY_SIGNUPS",
    DynamicSetting(
        "astrosat_users.UserSettings.notify_signups",
        env("DJANGO_ASTROSAT_USERS_NOTIFY_SIGNUPS", default=False),
    ),
)
