from rest_framework import serializers

from astrosat_users.models import Customer, CustomerUser, User, UserRole
from .serializers_users import UserSerializerBasic
from .serializers_auth import RegisterSerializer

# TODO: MOVE THIS TO django-astrosat-core
class ContextVariableDefault(object):
    """
    May be applied as a `default=...` value on a serializer field
    Returns the "variable_name" item from the serializer context.
    Raise an error on a missing item only if "raise_error" is True.
    """

    requires_context = True

    def __init__(self, variable_name, raise_error=False):
        self.variable_name = variable_name
        self.raise_error = raise_error

    def __call__(self, serializer_field):
        try:
            return serializer_field.context[self.variable_name]
        except KeyError as e:
            if self.raise_error:
                raise e


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("type", "name", "title", "description", "logo", "url", "roles", "country", "address", "postcode")

    type = serializers.CharField(source="customer_type")
    roles = serializers.SlugRelatedField(
        many=True, queryset=UserRole.objects.all(), slug_field="name"
    )


class CustomerUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerUser
        fields = ("id", "type", "status", "user", "customer")

    type = serializers.CharField(source="customer_user_type")
    status = serializers.CharField(source="customer_user_status")
    customer = serializers.SlugRelatedField(
        default=ContextVariableDefault("customer_name", raise_error=True),
        queryset=Customer.objects.all(),
        slug_field="name",
        write_only=True,
    )
    user = (
        UserSerializerBasic()
    )  # note I don't use the full UserSerializer b/c I don't need to serialize the customer

    # def create(self, validated_data):

    #     print("IFAFDAFDSF", flush=True)
    #     return None
    #     user_serializer = self.fields["user"]
    #     user_data = validated_data.pop(user_serializer.source)
    #     try:
    #         # existing user, just update them...
    #         user = User.objects.get(email=user_data["email"])
    #         user_serializer.update(user, user_data)
    #     except User.DoesNotExist:
    #         # new user, perform registration...
    #         user_registration_data = user_data.copy()
    #         user_registration_data.update(
    #             {"password1": "superpassword23", "password2": "superpassword23",}
    #         )

    #         # import pdb; pdb.set_trace()
    #         from django.http import QueryDict

    #         request = self.context["request"]
    #         # request.POST = QueryDict("", mutable=True)
    #         # request.POST.update(user_registration_data)
    #         request._data = user_registration_data
    #         user = RegisterSerializer(request).save()
    #         # complete_signup(
    #         #     self.request._request, user, allauth_settings.EMAIL_VERIFICATION, None
    #         # )
    #         user_serializer.update(user, user_data)
    #     validated_data["user"] = user
    #     validated_data[""]
    #     return super().create(validated_data)
