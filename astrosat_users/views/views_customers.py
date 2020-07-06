from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from rest_framework import generics, mixins, viewsets
from rest_framework.permissions import IsAuthenticated, BasePermission

from django_filters import rest_framework as filters

from astrosat_users.models import Customer, CustomerUser
from astrosat_users.serializers import CustomerSerializer, CustomerUserSerializer


class IsAdminOrManager(BasePermission):
    """
    Only the admin or a Customer Manager can access this view.
    (Relies on the property "active_managers" in the views below.)
    """

    def has_permission(self, request, view):
        user = request.user
        return user.is_superuser or view.active_managers.filter(user=user).exists()


class CustomerDetailView(generics.RetrieveUpdateAPIView):

    permission_classes = [IsAuthenticated, IsAdminOrManager]
    serializer_class = CustomerSerializer

    lookup_field = "id"

    @property
    def active_managers(self):
        customer = self.get_object()
        return customer.customer_users.managers().active()

    def get_object(self):
        if getattr(self, "swagger_fake_view", False):
            # object just for schema generation metadata (when there are no kwargs)
            # as per https://github.com/axnsan12/drf-yasg/issues/333#issuecomment-474883875
            return None

        return super().get_object()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            # queryset just for schema generation metadata
            # as per https://github.com/axnsan12/drf-yasg/issues/333#issuecomment-474883875
            return Customer.objects.none()

        return Customer.objects.multiple()


class CustomerUserFilterSet(filters.FilterSet):
    class Meta:
        model = CustomerUser
        fields = ("type", "status")

    type = filters.CharFilter(field_name="customer_user_type", lookup_expr="iexact")
    status = filters.CharFilter(field_name="customer_user_status", lookup_expr="iexact")


class CustomerUserViewMixin(object):

    # DRY way of customizing object retrieval for the 2 views below

    @cached_property
    def customer(self):
        customer_id = self.kwargs["id"]
        customer = get_object_or_404(Customer, id=customer_id)
        return customer

    @property
    def active_managers(self):
        return self.customer.customer_users.managers().active()

    def get_object(self):
        if getattr(self, "swagger_fake_view", False):
            # object just for schema generation metadata (when there are no kwargs)
            # as per https://github.com/axnsan12/drf-yasg/issues/333#issuecomment-474883875
            return None

        qs = self.get_queryset()
        qs = self.filter_queryset(qs)
        user_email = self.kwargs["email"]

        obj = get_object_or_404(qs, user__email=user_email)
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            # queryset just for schema generation metadata (when there are no kwargs)
            # as per https://github.com/axnsan12/drf-yasg/issues/333#issuecomment-474883875
            return CustomerUser.objects.none()

        return self.customer.customer_users.select_related("user").all()

    def get_serializer_context(self):
        # the customer is a write_only field on the serializer
        # therefore I don't always provide it, I use this extra context
        # to compute a default field value using ContextVariableDefault
        context = super().get_serializer_context()
        if getattr(self, "swagger_fake_view", False):
            context["customer"] = None
        else:
            context["customer"] = self.customer
        return context


class CustomerUserListView(CustomerUserViewMixin, generics.ListCreateAPIView):

    permission_classes = [IsAuthenticated, IsAdminOrManager]
    serializer_class = CustomerUserSerializer

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CustomerUserFilterSet


class CustomerUserDetailView(
    CustomerUserViewMixin, generics.RetrieveUpdateDestroyAPIView
):

    permission_classes = [IsAuthenticated, IsAdminOrManager]
    serializer_class = CustomerUserSerializer

    lookup_value_regex = (
        "[^/]+"  # the default regex was "[^/.]+" which wasn't matching email addresses
    )
