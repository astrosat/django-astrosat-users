import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.signals import user_logged_out
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from allauth.account.models import EmailAddress

from astrosat.utils import validate_no_tags

from astrosat_users.validators import ImageDimensionsValidator


def get_sentinel_user():
    """
    returns a "sentinel" object: the User to use as a placeholder
    for FKs if the original User gets deleted.
    """
    user, _ = User.objects.get_or_create(username="sentinel")
    return user


def user_avatar_path(instance, filename):
    return f"users/{instance.username}/{filename}"


class UserRegistrationStageType(models.TextChoices):

    USER = "USER", _("User")
    CUSTOMER = "CUSTOMER", _("Customer")
    CUSTOMER_USER = "CUSTOMER_USER", _("CustomerUser")
    ORDER = "ORDER", _("Order")

    __empty__ = _("None")


class User(AbstractUser):

    # TODO: CUSTOM MANAGER ?

    PROFILE_KEYS = []

    roles = models.ManyToManyField("UserRole", related_name="users", blank=True)

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)  # note that this is not the pk

    avatar = models.ImageField(
        upload_to=user_avatar_path,
        validators=[ImageDimensionsValidator()],
        blank=True,
        null=True,
    )

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
    accepted_terms = models.BooleanField(
        default=False, help_text=_("Has this user accepted the terms & conditions?")
    )
    registration_stage = models.CharField(
        blank=True, null=True, max_length=128, choices=UserRegistrationStageType.choices, help_text=_("Indicates which stage of the registration process a user is at.")
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

    def delete(self, *args, **kwargs):
        """
        When a user is deleted, delete the corresponding avatar storage.
        Doing it in a method instead of via signals to handle the case where objects are deleted in bulk.
        """
        if self.avatar:
            avatar_name = self.avatar.name
            avatar_storage = self.avatar.storage
            if avatar_storage.exists(avatar_name):
                avatar_storage.delete(avatar_name)

        return super().delete(*args, **kwargs)
