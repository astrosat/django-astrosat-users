from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

from astrosat.mixins import SingletonMixin


class UserSettings(SingletonMixin, models.Model):
    class Meta:
        verbose_name = "User Settings"
        verbose_name_plural = "User Settings"

    allow_registration = models.BooleanField(
        default=True,
        help_text=_("Allow users to register via the 'sign up' views.")
    )
    enable_backend_access = models.BooleanField(
        default=True,
        help_text=_(
            "Enable user management via the backend views (as opposed to only via the API)."
        ),
    )
    notify_signups = models.BooleanField(
        default=False,
        help_text=_("Send an email to the MANAGERS when a user signs up."),
    )
    require_approval = models.BooleanField(
        default=False,
        help_text=_("Require a formal approval step to the sign up process."),
    )
    require_terms_acceptance = models.BooleanField(
        default=False,
        help_text=_(
            "Require a user to accept the terms & conditions during the sign up process."
        ),
    )
    require_verification = models.BooleanField(
        default=True,
        help_text=_(
            "Require an email verification step to the sign up process."
        ),
    )

    password_min_length = models.PositiveIntegerField(
        default=6, help_text=_("Minimum length of a user password")
    )
    password_max_length = models.PositiveIntegerField(
        default=255, help_text=_("Maximum length of a user password")
    )

    password_strength = models.IntegerField(
        default=2,
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text=_(
            "Strength of password field as per <a href='github.com/dropbox/zxcvbn'>zxcvbn</a>"
        )
    )

    def __str__(self):
        return "User Settings"

    def clean(self):
        if self.password_max_length < self.password_min_length:
            raise ValidationError(
                "password_max_length must be greater than or equal to password_min_length."
            )
