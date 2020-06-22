from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, UpdateView

from rest_framework import mixins, viewsets
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS

from django_filters import rest_framework as filters

from astrosat.views import BetterBooleanFilter, BetterBooleanFilterField

from astrosat_users.models import User, UserRole, UserPermission
from astrosat_users.serializers import UserSerializer


##############
#  api views #
##############


class IsAdminOrSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        # anybody can do GET, HEAD, or OPTIONS
        if request.method in SAFE_METHODS:
            return True

        # only the admin or the specific user can do POST, PUT, PATCH, DELETE
        user = request.user
        return user.is_superuser or user == obj


class UserFilterSet(filters.FilterSet):
    class Meta:
        model = User
        fields = ["is_active", "is_approved", "accepted_terms", "is_verified"]

    is_active = BetterBooleanFilter()
    is_approved = BetterBooleanFilter()
    accepted_terms = BetterBooleanFilter()
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
        role_names = value.split(",")
        return queryset.filter(roles__name__in=role_names).distinct()

    def filter_roles_and(self, queryset, name, value):
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
    users is intentionally unsupported outside of the Django Admin.
    """

    pass


class UserViewSet(ListRetrieveViewSet):

    permission_classes = [IsAuthenticated, IsAdminOrSelf]
    serializer_class = UserSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = UserFilterSet

    queryset = User.objects.prefetch_related("roles", "roles__permissions")

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


#################
# backend views #
#################

# just some lightweight views for clients that don't use the API
# (not really expecting any of these to be used in anger)


@method_decorator(
    login_required(login_url=reverse_lazy("account_login")), name="dispatch"
)
class UserListView(ListView):

    model = User

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(is_active=True)


@method_decorator(
    login_required(login_url=reverse_lazy("account_login")), name="dispatch"
)
class UserDetailView(DetailView):

    model = User
    slug_field = "email"
    slug_url_kwarg = "email"


@method_decorator(
    login_required(login_url=reverse_lazy("account_login")), name="dispatch"
)
class UserUpdateView(UpdateView):
    model = User
    fields = ("name", "description")
    slug_field = "email"
    slug_url_kwarg = "email"
    template_name_suffix = (
        "_update"
    )  # override stupid default template_name_suffix of "_form"

    def get_object(self, *args, **kwargs):

        obj = super().get_object(*args, **kwargs)

        current_user = self.request.user
        if current_user != obj and not current_user.is_superuser:
            raise PermissionDenied()
        return obj
