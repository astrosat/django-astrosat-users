from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.signals import user_logged_out
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from allauth.account.models import EmailAddress

from astrosat.mixins import SingletonMixin
from astrosat.utils import validate_no_tags


def get_sentinel_user():
    """
    returns a "sentinel" object: the User to use as a placeholder
    for FKs if the original User gets deleted.
    """
    user, _ = User.objects.get_or_create(username="sentinel")
    return user


class User(AbstractUser):

    # objects = (
    #     UserManager()
    # )  # see the note in "managers.py" explaining why I'm not just using "UserQuerySet.as_manager()" here

    PROFILE_KEYS = []

    # a bit of cleverness here...
    # jwt will use USERNAME_FIELD for logging in
    # but astrosat_users uses the email address
    # but that's already defined as a REQUIRED_FIELD in AbstractUser
    # so I have to redefine _both_ REQUIRED_FIELD _and_ USERNAME_FIELD
    # (and potentially ensure that email is unique)
    # REQUIRED_FIELDS = ["username"]
    # USERNAME_FIELD = "email"

    roles = models.ManyToManyField("UserRole", related_name="users", blank=True)

    name = models.CharField(
        validators=[validate_no_tags], blank=True, null=True, max_length=255
    )
    description = models.TextField(validators=[validate_no_tags], blank=True, null=True)
    change_password = models.BooleanField(
        default=False, help_text=_("Force user to change password at next login.")
    )
    is_approved = models.BooleanField(
        default=False, help_text=_("Has this user been approved?")
    )
    latest_confirmation_key = models.CharField(
        blank=True,
        null=True,
        max_length=64,
        help_text=_(
            "A record of the most recent key used to verify the user's email address."
        ),
    )

    def get_absolute_url(self):
        return reverse("user-detail", kwargs={"email": self.email})

    @property
    def profiles(self):
        """
        Returns all profiles associated w/ this user.
        """
        return {
            profile_key: getattr(self, profile_key, None)
            for profile_key in self.PROFILE_KEYS
        }

    @property
    def is_verified(self):
        """
        Checks if the primary email address belonging to this user has been verified.
        """
        return (
            self.emailaddress_set.only("verified", "primary")
            .filter(primary=True, verified=True)
            .exists()
        )

    def logout_all(self):
        """
        Logs a user out of all sessions.
        """
        self.auth_token_set.all().delete()
        user_logged_out.send(sender=User, request=None, user=self)

    def verify(self):
        """
        Manually verifies a user's primary email address
        """

        emailaddresses = self.emailaddress_set.all()

        try:
            primary_emailaddress = emailaddresses.get(primary=True)
        except EmailAddress.DoesNotExist:
            primary_emailaddress, _ = EmailAddress.objects.get_or_create(
                user=self, email=self.email
            )
            primary_emailaddress.set_as_primary(conditional=True)

        primary_emailaddress.verified = True
        primary_emailaddress.save()
