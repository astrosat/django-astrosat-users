from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework.utils.encoders import JSONEncoder

from allauth.account.adapter import get_adapter

from django_filters import rest_framework as filters

from astrosat_users.models import Customer, CustomerUser
from astrosat_users.models.models_customers import CustomerUserType
from astrosat_users.models.models_users import UserRegistrationStageType
from astrosat_users.serializers import CustomerSerializer, CustomerUserSerializer
from astrosat_users.views.views_users import UserRegistrationStagePermission


class IsAdminOrManager(BasePermission):
    """
    Only the admin or a Customer Manager can access this view.
    (Relies on the property "active_managers" in the views below.)
    """

    message = "Only a customer manager can perform this action."

    def has_permission(self, request, view):
        user = request.user
        return user.is_superuser or view.active_managers.filter(user=user).exists()


class CannotDeleteSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method == "DELETE":
            return user != obj.user

        return True


class CustomerViewMixin(object):

    # DRY way of customizing object retrieval for the 2 views below

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


class CustomerCreateView(CustomerViewMixin, generics.CreateAPIView):

    lookup_field = "id"
    lookup_url_kwarg = "customer_id"

    permission_classes = (
        IsAuthenticated,
        UserRegistrationStagePermission(UserRegistrationStageType.CUSTOMER)
    )
    serializer_class = CustomerSerializer

    def perform_create(self, serializer):
        customer = serializer.save()
        user = self.request.user
        if user.registration_stage == UserRegistrationStageType.CUSTOMER:
            user.registration_stage = str(UserRegistrationStageType.CUSTOMER_USER)
            user.save()
        return customer

class CustomerUpdateView(CustomerViewMixin, generics.RetrieveUpdateAPIView):

    lookup_field = "id"
    lookup_url_kwarg = "customer_id"

    permission_classes = [IsAuthenticated, IsAdminOrManager]
    serializer_class = CustomerSerializer

    def perform_update(self, serializer):

        existing_customer = self.get_object()
        updated_customer = serializer.save()

        json_encoder = JSONEncoder()
        existing_customer_data = json_encoder.encode(self.serializer_class(existing_customer).data)
        updated_customer_data = json_encoder.encode(serializer.data)

        if existing_customer_data != updated_customer_data:
            adapter = get_adapter(self.request)
            context = {
                "customer": updated_customer,
            }
            managers_emails = updated_customer.customer_users.managers().values_list("user__email", flat=True)
            adapter.send_mail("astrosat_users/email/update_customer", managers_emails, context)

        return updated_customer


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
        customer_id = self.kwargs["customer_id"]
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
        user_uuid = self.kwargs["user_id"]

        obj = get_object_or_404(qs, user__uuid=user_uuid)
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

    permission_classes = [
        IsAuthenticated &
        (IsAdminOrManager | UserRegistrationStagePermission(UserRegistrationStageType.CUSTOMER_USER))
    ]

    serializer_class = CustomerUserSerializer

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CustomerUserFilterSet

    def perform_create(self, serializer):
        user = self.request.user

        customer_user = serializer.save()
        if user != customer_user.user:
            customer_user.invite(adapter=get_adapter(self.request))

        if user.registration_stage == UserRegistrationStageType.CUSTOMER_USER:
            user.registration_stage = None
            user.save()

        return customer_user


class CustomerUserDetailView(CustomerUserViewMixin, generics.RetrieveUpdateDestroyAPIView):

    permission_classes = [IsAuthenticated, IsAdminOrManager, CannotDeleteSelf]
    serializer_class = CustomerUserSerializer

    def perform_destroy(self, instance):
        deleted_instances = instance.uninvite(adapter=get_adapter(self.request))
        if not(deleted_instances):  # only proceed w/ the deletion if "uninvite" hasn't already done it
            return super().perform_destroy(instance)

    def perform_update(self, serializer):

        existing_customer_user = self.get_object()
        updated_customer_user = serializer.save()

        json_encoder = JSONEncoder()
        existing_customer_user_user_data = json_encoder.encode(self.serializer_class(existing_customer_user).data["user"])
        updated_customer_user_user_data = json_encoder.encode(serializer.data["user"])

        adapter = get_adapter(self.request)
        context = {
            "user": updated_customer_user.user,
            "customer": updated_customer_user.customer,
        }
        managers_emails = self.customer.customer_users.managers().values_list("user__email", flat=True)

        if existing_customer_user_user_data != updated_customer_user_user_data:
            template_prefix = "astrosat_users/email/update_user"
            adapter.send_mail(template_prefix, updated_customer_user.user.email, context, cc=managers_emails)

        if existing_customer_user.customer_user_type != updated_customer_user.customer_user_type:

            if updated_customer_user.customer_user_type == CustomerUserType.MANAGER:
                # customer_user was something else, now it's a MANAGER
                template_prefix = "astrosat_users/email/admin_assign"
            elif existing_customer_user.customer_user_type == CustomerUserType.MANAGER:
                # customer_user was a MANAGER, now it's something else
                template_prefix = "astrosat_users/email/admin_revoke"

            adapter.send_mail(template_prefix, updated_customer_user.user.email, context, cc=managers_emails)

        return updated_customer_user


class CustomerUserInviteView(CustomerUserViewMixin, generics.GenericAPIView):
    """
    A special view just for re-sending invitations.
    """

    permission_classes = [IsAuthenticated, IsAdminOrManager]
    serializer_class = CustomerUserSerializer

    def post(self, request, *args, **kwargs):
        customer_user = self.get_object()
        customer_user.invite(adapter=get_adapter(request))
        serializer = self.get_serializer(customer_user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomerUserOnboardView(CustomerUserViewMixin, generics.GenericAPIView):
    """
    A special view just for onboarding Users.
    """

    permission_classes = [IsAuthenticated, IsAdminOrManager]
    serializer_class = CustomerUserSerializer

    def post(self, request, *args, **kwargs):
        customer_user = self.get_object()
        customer_user.user.onboard(adapter=get_adapter(request), customer=self.customer)
        serializer = self.get_serializer(customer_user)
        return Response(serializer.data, status=status.HTTP_200_OK)
