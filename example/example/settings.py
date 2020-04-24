"""
Django settings for example project.

Generated by 'django-admin startproject' using Django 2.2.6.
"""

import environ
import importlib
import os

from django.utils.html import escape
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from astrosat.utils import DynamicSetting


env = environ.Env()

PROJECT_NAME = "Example Project"
PROJECT_SLUG = slugify(PROJECT_NAME)
PROJECT_EMAIL = "{role}@astrosat.space"

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = "shhh..."

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # api...
    "rest_framework",
    "django_filters",
    "drf_yasg",
    "knox",
    # users...
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "rest_auth",
    "rest_auth.registration",
    # "rest_framework.authtoken",
    # astrosat...
    "astrosat",
    "astrosat_users",
    # this app...
    "example",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "example.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            # I override some built-in templates (rest_framework, allauth, & rest_auth)
            # in order for this to work, I need to make sure that the following directories are checked
            # before their default locations (see the comment in "loaders" for more info)
            os.path.join(BASE_DIR, "example/templates/"),
            os.path.join(
                os.path.dirname(importlib.import_module("astrosat_users").__file__),
                "templates",
            ),
        ],
        # 'APP_DIRS': True,
        "OPTIONS": {
            "loaders": [
                # first look at files in DIR, then look in the standard place for each INSTALLED_APP
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "example.wsgi.application"

# Migrations
# hard-coded migration to set sites table
MIGRATION_MODULES = {"sites": "example.contrib.sites.migrations"}

SITE_ID = 1

# Database

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

# API

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # "rest_framework.authentication.BasicAuthentication",  # insecure
        # "rest_framework.authentication.SessionAuthentication",  # CSRF
        # "rest_framework.authentication.TokenAuthentication",  # tokens
        "knox.auth.TokenAuthentication"  # better tokens
    ]
}

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Token Authentication": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": escape("Enter 'Token <key>'"),
        }
    },
    "DOC_EXPANSION": "none",
    "OPERATIONS_SORTER": None,
    "TAGS_SORTER": "alpha",
    "DEFAULT_MODEL_RENDERING": "example",
}

# Authentication / Users

LOGIN_URL = "account_login"
LOGOUT_URL = "account_logout"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

AUTH_USER_MODEL = "astrosat_users.User"

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

ACCOUNT_ADAPTER = "astrosat_users.adapters.AccountAdapter"
SOCIALACCOUNT_ADAPTER = "astrosat_users.adapters.SocialAccountAdapter"

ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 5
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_USERNAME_BLACKLIST = ["admin", "sentinel"]

ACCOUNT_FORMS = {
    # "add_email": "allauth.account.forms.AddEmailForm",
    # "change_password": "allauth.account.forms.ChangePasswordForm",
    # "disconnect": "allauth.socialaccount.forms.DisconnectForm",
    "login": "astrosat_users.forms.LoginForm",
    "reset_password": "astrosat_users.forms.PasswordResetForm",
    # "reset_password_from_key": "allauth.account.forms.ResetPasswordKeyForm",
    # "set_password": "allauth.account.forms.SetPasswordForm",
    "signup": "astrosat_users.forms.RegistrationForm",

}

REST_AUTH_SERIALIZERS = {
    "TOKEN_SERIALIZER": "astrosat_users.serializers.KnoxTokenSerializer",
    "LOGIN_SERIALIZER": "astrosat_users.serializers.LoginSerializer",
    "PASSWORD_CHANGE_SERIALIZER": "astrosat_users.serializers.PasswordChangeSerializer",
    "PASSWORD_RESET_SERIALIZER": "astrosat_users.serializers.PasswordResetSerializer",
    "PASSWORD_RESET_CONFIRM_SERIALIZER": "astrosat_users.serializers.PasswordResetConfirmSerializer",
}

REST_AUTH_REGISTER_SERIALIZERS = {
    "REGISTER_SERIALIZER": "astrosat_users.serializers.RegisterSerializer"
}

REST_AUTH_TOKEN_MODEL = "knox.models.AuthToken"  # model class for tokens, default value rest_framework.authtoken.models
REST_AUTH_TOKEN_CREATOR = "astrosat_users.utils.create_knox_token"  # - callable to create tokens, default value rest_auth.utils.default_create_token.
# REST_SESSION_LOGIN - Enable session login in Login API view (default: True)
# REST_USE_JWT - Enable JWT Authentication instead of Token/Session based. This is built on top of django-rest-framework-jwt (default: False)
# OLD_PASSWORD_FIELD_ENABLED - set it to True if you want to have old password verification on password change enpoint (default: False)
# LOGOUT_ON_PASSWORD_CHANGE - set to False if you want to keep the current user logged in after a password change


# Password validation


PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 255
PASSWORD_STRENGTH = 2

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "astrosat_users.utils.LengthPasswordValidator",
        "OPTIONS": {
            "min_length": PASSWORD_MIN_LENGTH,
            "max_length": PASSWORD_MAX_LENGTH,
        },
    },
    {
        "NAME": "astrosat_users.utils.StrengthPasswordValidator",
        "OPTIONS": {"strength": PASSWORD_STRENGTH},
    },
]

# Emailing

# (don't really send email in this example project...)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# (...and don't really send it to/from these people...)
ADMINS = [(PROJECT_NAME, PROJECT_EMAIL.format(role="noreply"))]
MANAGERS = ADMINS

DEFAULT_FROM_EMAIL = f"{PROJECT_NAME} <{PROJECT_EMAIL.format(role='noreply')}>"

# Internationalization

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [("en-us", _("American English")), ("en-gb", _("British English"))]

LOCALE_PATHS = [os.path.join(BASE_DIR, "locale")]


# Static files (CSS, JavaScript, Images)

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Profiling

if DEBUG:

    # see "https://gist.github.com/douglasmiranda/9de51aaba14543851ca3"
    # for more tips about making django_debug_toolbar to play nicely w/ Docker

    import socket

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())

    INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]
    INTERNAL_IPS += [ip[:-1] + "1" for ip in ips]

    INSTALLED_APPS += ["debug_toolbar", "pympler"]  # noqa F405
    MIDDLEWARE += [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        "astrosat.middleware.JSONDebugToolbarMiddleware",
    ]  # noqa F405
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TEMPLATE_CONTEXT": True,
        "SHOW_COLLAPSED": True,
        "SHOW_TOOLBAR_CALLBACK": "astrosat.utils.show_toolbar",
    }
    DEBUG_TOOLBAR_PANELS = [
        "debug_toolbar.panels.versions.VersionsPanel",
        "debug_toolbar.panels.timer.TimerPanel",
        "debug_toolbar.panels.settings.SettingsPanel",
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",
        "debug_toolbar.panels.profiling.ProfilingPanel",
        "debug_toolbar.panels.cache.CachePanel",
        "debug_toolbar.panels.signals.SignalsPanel",
        "debug_toolbar.panels.staticfiles.StaticFilesPanel",
        "debug_toolbar.panels.templates.TemplatesPanel",
        "debug_toolbar.panels.logging.LoggingPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
    ]
