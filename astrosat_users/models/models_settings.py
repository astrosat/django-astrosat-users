from django.db import models
from django.utils.translation import gettext_lazy as _

from astrosat.mixins import SingletonMixin


class UserSettings(SingletonMixin, models.Model):
    class Meta:
        verbose_name = "User Settings"
        verbose_name_plural = "User Settings"

    allow_registration = models.BooleanField(
        default=True, help_text=_("Allow users to register via the 'sign up' view.")
    )
    enable_backend_access = models.BooleanField(
        default=True,
        help_text=_(
            "Enable user management via the backend views (as opposed to only the API)."
        ),
    )
    notify_signups = models.BooleanField(
        default=False, help_text=_("Send an email to the admin when a user signs up.")
    )
    require_approval = models.BooleanField(
        default=False,
        help_text=_("Require a formal approval step to the sign up process."),
    )
    require_verification = models.BooleanField(
        default=True,
        help_text=_("Require an email verification step to the sign up process."),
    )

    def __str__(self):
        return "User Settings"
