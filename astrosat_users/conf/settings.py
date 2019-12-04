import environ

from django.conf import settings
from django.utils.text import slugify

from astrosat.utils import DynamicSetting

from .. import APP_NAME

env = environ.Env()


PROJECT_NAME = getattr(settings, "PROJECT_NAME", "Django Astrosat Users")
PROJECT_SLUG = getattr(settings, "PROJECT_SLUG", slugify(PROJECT_NAME))
PROJECT_EMAIL = getattr(settings, "PROJECT_EMAIL", "{role}@astrosat.space")

ACCOUNT_CONFIRM_EMAIL_CLIENT_URL = getattr(
    settings, "ACCOUNT_CONFIRM_EMAIL_CLIENT_URL", "verify-email/?key={key}"
)
ACCOUNT_CONFIRM_PASSWORD_CLIENT_URL = getattr(
    settings, "ACCOUNT_CONFIRM_PASSWORD_CLIENT_URL", "confirm-pwd/?key={key}&uid={uid}"
)


PASSWORD_MIN_LENGTH = getattr(settings, "PASSWORD_MIN_LENGTH", 8)
PASSWORD_MAX_LENGTH = getattr(settings, "PASSWORD_MAX_LENGTH", 255)
PASSWORD_STRENGTH = getattr(settings, "PASSWORD_STRENGTH", 2)

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


# required third party settings...
# (most of these are checked in checks.py)

LOGIN_REDIRECT_URL = getattr(settings, "LOGIN_REDIRECT_URL", "/")
LOGOUT_REDIRECT_URL = getattr(settings, "LOGOUT_REDIRECT_URL", "/")
VERIFICATION_REDIRECT_URL = getattr(settings, "VERIFICATION_REDIRECT_URL", "/")
APPROVAL_REDIRECT_URL = getattr(settings, "APPROVAL_REDIRECT_URL", "/")

ALLAUTH_SETTINGS = {
    "ACCOUNT_ADAPTER": f"{APP_NAME}.adapters.AccountAdapter",
    "SOCIALACCOUNT_ADAPTER": f"{APP_NAME}.adapters.SocialAccountAdapter",
    "ACCOUNT_AUTHENTICATION_METHOD": "email",
    "ACCOUNT_USERNAME_REQUIRED": False,
    "ACCOUNT_EMAIL_REQUIRED": True,
    "ACCOUNT_LOGIN_ATTEMPTS_LIMIT": 5,
    "ACCOUNT_LOGOUT_ON_GET": False,
    "ACCOUNT_USERNAME_BLACKLIST": ["admin", "sentinel"],
    "ACCOUNT_FORMS": {
        # "add_email": "allauth.account.forms.AddEmailForm",
        # "change_password": "allauth.account.forms.ChangePasswordForm",
        "login": "astrosat_users.forms.LoginForm",
        "reset_password": "astrosat_users.forms.PasswordResetForm",
        # "reset_password_from_key": "allauth.account.forms.ResetPasswordKeyForm",
        # "set_password": "allauth.account.forms.SetPasswordForm",
        # "signup": "allauth.account.forms.SignupForm",
    },
}

REST_AUTH_SETTINGS = {
    "REST_AUTH_SERIALIZERS": {
        "TOKEN_SERIALIZER": "astrosat_users.serializers.KnoxTokenSerializer",
        "LOGIN_SERIALIZER": "astrosat_users.serializers.LoginSerializer",
        "PASSWORD_CHANGE_SERIALIZER": "astrosat_users.serializers.PasswordChangeSerializer",
        "PASSWORD_RESET_SERIALIZER": "astrosat_users.serializers.PasswordResetSerializer",
        "PASSWORD_RESET_CONFIRM_SERIALIZER": "astrosat_users.serializers.PasswordResetConfirmSerializer",
    },
    "REST_AUTH_REGISTER_SERIALIZERS": {
        "REGISTER_SERIALIZER": "astrosat_users.serializers.RegisterSerializer"
    },
    "REST_AUTH_TOKEN_MODEL": "knox.models.AuthToken",
    "REST_AUTH_TOKEN_CREATOR": "astrosat_users.utils.create_knox_token",
}
