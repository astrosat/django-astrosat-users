from rest_framework.permissions import (
    IsAuthenticated,
    IsAdminUser,
    BasePermission,
    SAFE_METHODS,
)
from rest_framework import mixins, viewsets

from astrosat_users.models import User, UserRole, UserPermission
from astrosat_users.serializers import (
    UserSerializer,
    UserRoleSerializer,
    UserPermissionSerializer,
)


class IsAdminOrSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        # anybody can do GET, HEAD, or OPTIONS
        if request.method in SAFE_METHODS:
            return True

        # only the admin or the specific user can do POST, PUT, PATCH, DELETE
        user = request.user
        return user.is_superuser or user == obj


class ListRetrieveViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    A generic viewset for listing, retrieving, and updating models.
    But not creating or deleting them.  Used by all ViewSets below.
    Creating users is done via the KnoxRegisterView. And deleting
    users is unsupported outside of the Django Admin.
    """

    pass


class UserViewSet(ListRetrieveViewSet):

    permission_classes = [IsAuthenticated, IsAdminOrSelf]
    serializer_class = UserSerializer
    queryset = User.objects.filter(is_active=True).prefetch_related(
        "roles", "roles__permissions"
    )
    lookup_field = "email"
    lookup_value_regex = (
        "[^/]+"
    )  # the default regex was "[^/.]+" which wasn't matching email addresses

    def get_serializer_context(self):
        context = super().get_serializer_context()

        # TODO: ADD SOME LOGIC HERE TO RESTRICT WHICH PROFILES WE CAN SERIALIZE
        # TODO: (NOT ALL USERS SHOULD MODIFY ALL PROFILES)
        managed_profiles = [profile_key for profile_key in User.PROFILE_KEYS]

        context.update({"managed_profiles": managed_profiles})
        return context

    def get_object(self, *args, **kwargs):
        """
        If you passed the reserved word "current",
        return the user making the request.
        """
        if self.kwargs.get(self.lookup_field).upper() == "CURRENT":
            return self.request.user

        return super().get_object(*args, **kwargs)


class UserRoleViewSet(ListRetrieveViewSet):

    permission_classes = [IsAdminUser]
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    lookup_field = "name"


class UserPermissionViewSet(ListRetrieveViewSet):

    permission_classes = [IsAdminUser]
    queryset = UserPermission.objects.all()
    serializer_class = UserPermissionSerializer
    lookup_field = "name"
