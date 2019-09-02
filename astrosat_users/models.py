from collections import OrderedDict

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from allauth.account.models import EmailAddress

from astrosat.mixins import SingletonMixin
from astrosat.utils import validate_no_tags

from .managers import UserManager
from .tokens import default_token_generator
from .conf import app_settings


RESERVED_USERNAMES = ["CURRENT", "DELETED"]  # some names could interfere w/ the API


def get_deleted_user():
    """
    Returns a special "deleted" user to use in objects
    w/ a foreign_key to User where that user has been deleted.
    """
    deleted_user, _ = User.objects.get_or_create(username='DELETED')
    return deleted_user

############
# settings #
############

class UserSettings(SingletonMixin, models.Model):

    class Meta:
        verbose_name = "User Settings"
        verbose_name_plural = "User Settings"

    allow_registration = models.BooleanField(default=True, help_text=_("Allow users to register via the 'sign up' view."))
    enable_backend_access = models.BooleanField(default=True, help_text=_("Enable user management via the backend views (as opposed to only the API)."))
    notify_signups = models.BooleanField(default=False, help_text=_("Send an email to the admin when a user signs up."))
    require_approval = models.BooleanField(default=False, help_text=_("Require a formal approval step to the sign up process."))
    require_verification = models.BooleanField(default=True, help_text=_("Require an email verification step to the sign up process."))

    def __str__(self):
        return "User Settings"


####################
# the actual model #
####################


class User(AbstractUser):

    objects = UserManager()  # see the note in "managers.py" explaining why I'm not just using "UserQuerySet.as_manager()" here

    profile_keys = []

    @property
    def profiles(self):
        """
        Returns all profiles associated w/ this user.
        """
        return {
            profile_key: getattr(self, profile_key, None)
            for profile_key in self.profile_keys
        }

    name = models.CharField(validators=[validate_no_tags], blank=True, null=True, max_length=255)
    description = models.TextField(validators=[validate_no_tags], blank=True, null=True)
    change_password = models.BooleanField(default=False, help_text=_("Force user to change password at next login."))
    is_approved = models.BooleanField(default=False, help_text=_("Has this user been approved?"))
    latest_confirmation_key = models.CharField(blank=True, null=True, max_length=64, help_text=_("A record of the most recent key used to verify the user's email address."))

    def clean_username(self):
        """
        Prevents users from being called anything in RESERVED_USERNAMES
        """

        # a _correct_ way to do this is to overwrite `clean` and call 'full_clean' in save
        # but that would force _all_ checks to run and I still want to allow users w/out passwords
        # another _correct_ way to do this is to explicitly add a regex validator to the username field
        # but I am wary of overloading username from AbstractUser in-case things change in the future
        # so I'm doings things _this_ way...

        if self.username.upper() in RESERVED_USERNAMES:
            errors = {
                "username": "username cannot be one of {0}.".format(", ".join(map("'{0}'".format, RESERVED_USERNAMES)))
            }
            raise ValidationError(errors)

    def get_absolute_url(self):
        return reverse("users-detail", kwargs={"username": self.username})

    @property
    def is_verified(self):
        """
        Checks if the primary email address belonging to this user has been verified.
        """
        return self.emailaddress_set.only("verified", "primary").filter(primary=True, verified=True).exists()

    def generate_token(self, token_generator=default_token_generator):
        return token_generator.make_token(self)

    def verify(self):
        """
        Manually verifies a user's primary email address
        """

        emailaddresses = self.emailaddress_set.all()

        try:
            primary_emailaddress = emailaddresses.get(primary=True)
        except EmailAddress.DoesNotExist:
            primary_emailaddress, _ = EmailAddress.objects.get_or_create(
                user=self,
                email=self.email,
            )
            primary_emailaddress.set_as_primary(conditional=True)

        primary_emailaddress.verified = True
        primary_emailaddress.save()

    def save(self, *args, **kwargs):
        self.clean_username()
        super().save(*args, **kwargs)
