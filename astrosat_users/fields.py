from django.conf import settings
from django.db import models
from django.db.models.fields.related import OneToOneField
from django.forms import ModelChoiceField
from django.utils.module_loading import import_string

from astrosat_users.models import PROFILES_REGISTRY
from astrosat_users.serializers.serializers_profiles import (
    GenericProfileSerializerFactory,
)


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
    (keyed by "related_name").  All possible profile classess are stored in the PROFILES dictionary above.
    """
    def __init__(self, *args, **kwargs):

        self.key = kwargs.get("related_name", None)
        self.serializer_class = kwargs.pop("serializer_class", None)
        assert (
            self.key is not None
        ), "'related_name' must be specified for UserProfileField."

        kwargs.update({
            "unique": True,
            "on_delete": models.CASCADE,
            "to": settings.AUTH_USER_MODEL,
        })
        super().__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name, **kwargs):
        """
        Updates the PROFILES dictionary w/ this class.
        Adds the key to the profile class.
        And sets the serializer class (either a custom one passed in __init__
        or the generic one).
        """

        assert name == "user", "UserProfileField must be called 'user'."

        super().contribute_to_class(cls, name, **kwargs)

        setattr(cls, "key", self.key)
        PROFILES_REGISTRY.register(cls)

        # using lambdas to pass a fn which gets the serializer on-demand
        # instead of trying to get it inline here (which could result in circular dependencies)
        if self.serializer_class is not None:
            get_serializer_fn = lambda *args: import_string(
                self.serializer_class
            )
        else:
            get_serializer_fn = lambda *args: GenericProfileSerializerFactory(
                cls
            )
        setattr(cls, "get_serializer_class", get_serializer_fn)

    def contribute_to_related_class(self, cls, related):
        """
        Adds the key to the User class (so that the @profiles property will work).
        """

        super().contribute_to_related_class(cls, related)

        profile_keys = getattr(cls, "PROFILE_KEYS", [])
        profile_keys.append(self.key)
        setattr(cls, "PROFILE_KEYS", profile_keys)

    def formfield(self, **kwargs):
        """
        Makes sure we can't change the User a Profile is linked to.
        """

        defaults = {"form_class": ModelChoiceField, "disabled": True}
        defaults.update(kwargs)
        return super().formfield(**defaults)
