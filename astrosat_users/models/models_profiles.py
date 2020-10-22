from itertools import chain

from django.core.exceptions import ImproperlyConfigured

# UserProfiles are defined in other apps via the UserProfileField
# but a registry of them is stored and manipulated here


class UserProfileRegistry(dict):
    """
    The registry is just a dictionary w/ some clever indirection
    for registering/unregistering models and better error-handling.
    """

    key = None

    def __init__(self, *args, **kwargs):
        self.key = kwargs.pop("key")
        super().__init__(*args, **kwargs)

    def __missing__(self, key):
        raise ImproperlyConfigured(
            f"No UserProfile has been registered w/ the key '{key}'."
        )

    def __getitem__(self, obj):
        # you can either access the registry w/ an object
        # (which has a key attribute), or the key itself
        key = getattr(obj, self.key, obj)
        return super().__getitem__(key)

    def register(self, obj):
        try:
            key = getattr(obj, self.key)
            self[key] = obj
        except AttributeError:
            raise NotImplementedError(
                f"'{self.key}' is a required attribute of '{obj}'"
            )

    def unregister(self, obj):
        key = getattr(obj, self.key, obj)
        try:
            self.pop(key)
        except KeyError:
            raise ImproperlyConfigured(
                f"No UserProfile has been registered w/ the key '{key}'"
            )


PROFILES_REGISTRY = UserProfileRegistry(key="key")


def get_profiles_qs():
    """
    combines all distinct UserProfile models into a single queryset
    """
    profile_querysets = [
        profile_class.objects.all()
        for profile_class in PROFILES_REGISTRY.values()
    ]
    return chain(*profile_querysets)
