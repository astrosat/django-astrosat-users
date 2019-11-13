from itertools import chain

from django.conf import settings
from django.db import models
from django.db.models.fields.related import OneToOneField
from django.forms import ModelChoiceField


PROFILES = {}


def get_profile_qs():
    profile_querysets = [
        profile_class.objects.all() for profile_class in PROFILES.values()
    ]
    # clever way of combining multiple querysets
    return chain(*profile_querysets)


class UserProfileField(OneToOneField):

    """
    A special field to use when defining a UserProfile.

    Usage is:
    > class MyUserProfile(models.Model):
    >   user = UserProfileField(related_name="my_user_profile")

    This will create a one-to-one relationship between the profile and the user. Creating
    the profile must still be done (using signals is a good way to do this).  Each profile
    added to a user can be accessed using the "related_name" kwarg.  Additionally, the
    "user@profiles" property returns a dictionary of all profiles belonging to a user
    (keyed by "related_name").  All possible profiles are stored in the PROFILES dictionary above.
    """

    def __init__(self, *args, **kwargs):

        self.key = kwargs.get("related_name", None)
        assert (
            self.key is not None
        ), "'related_name' must be specified for UserProfileField."

        kwargs.update(
            {
                "unique": True,
                "on_delete": models.CASCADE,
                "to": settings.AUTH_USER_MODEL,
            }
        )
        super().__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name, **kwargs):
        """
        Adds the key to the profile class.
        Updates the PROFILES dictionary w/ this class.
        """

        assert name == "user", "UserProfileField must be called 'user'."

        super().contribute_to_class(cls, name, **kwargs)

        setattr(cls, "key", self.key)

        PROFILES[self.key] = cls

    def contribute_to_related_class(self, cls, related):
        """
        Adds the key to the User class (so that the @profiles property will work).
        """

        super().contribute_to_related_class(cls, related)

        profile_keys = getattr(cls, "profile_keys", [])
        profile_keys.append(self.key)
        setattr(cls, "profile_keys", profile_keys)

    def formfield(self, **kwargs):
        """
        Makes sure we can't change the User a Profile is linked to.
        """

        defaults = {"form_class": ModelChoiceField, "disabled": True}
        defaults.update(kwargs)
        return super().formfield(**defaults)
