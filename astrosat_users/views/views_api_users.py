from django.core.exceptions import ValidationError
from django.db.models import Count

from rest_framework.permissions import (
    IsAuthenticated,
    IsAdminUser,
    BasePermission,
    SAFE_METHODS,
)
from rest_framework import mixins, viewsets
from rest_framework.exceptions import APIException

from django_filters import rest_framework as filters

from astrosat.views import BetterBooleanFilter, BetterBooleanFilterField

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


class UserFilterSet(filters.FilterSet):
    class Meta:
        model = User
        fields = ["is_active", "is_approved", "is_verified", "roles"]

    is_active = BetterBooleanFilter()
    is_approved = BetterBooleanFilter()
    is_verified = filters.Filter(method="filter_is_verified")
    roles__any = filters.Filter(method="filter_roles_or")
    roles__all = filters.Filter(method="filter_roles_and")
    permissions__any = filters.Filter(method="filter_permissions_or")
    permissions__all = filters.Filter(method="filter_permissions_and")

    def filter_is_verified(self, queryset, name, value):
        try:
            field = BetterBooleanFilterField()
            cleaned_value = field.clean(value)
            if cleaned_value is not None:
                # Django cannot efficiently filter querysets by property
                # so this basically recreates the logic of the @is_verified User property
                queryset = queryset.filter(
                    emailaddress__primary=True, emailaddress__verified=cleaned_value
                )
        except ValidationError as e:
            raise APIException({name: e.messages})
        return queryset

    def filter_roles_or(self, queryset, name, value):
        # this is the default behavior of the "__in" lookup; it's pretty straightforward
        role_names = value.split(",")
        return queryset.filter(roles__name__in=role_names).distinct()

    def filter_roles_and(self, queryset, name, value):
        # this uses annotations to match users w/ the same number of roles as the values
        # I'm not sure why I can't do something clever w/ Q objects like:
        # return queryset.filter(reduce(and_, map(lambda x: Q(roles__name=x), role_names)))
        role_names = value.split(",")
        return (
            queryset.filter(roles__name__in=role_names)
            .annotate(num_roles=Count("roles"))
            .filter(num_roles=len(role_names))
        )

    def filter_permissions_or(self, queryset, name, value):
        permission_names = value.split(",")
        return queryset.filter(roles__permissions__name__in=permission_names).distinct()

    def filter_permissions_and(self, queryset, name, value):
        permission_names = value.split(",")
        return (
            queryset.filter(roles__permissions__name__in=permission_names)
            .annotate(num_permissions=Count("roles__permissions"))
            .filter(num_permissions=len(permission_names))
        )


class UserViewSet(ListRetrieveViewSet):

    permission_classes = [IsAuthenticated, IsAdminOrSelf]
    serializer_class = UserSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = UserFilterSet

    queryset = User.objects.all().prefetch_related("roles", "roles__permissions")

    lookup_field = "email"
    lookup_value_regex = (
        "[^/]+"  # the default regex was "[^/.]+" which wasn't matching email addresses
    )

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
