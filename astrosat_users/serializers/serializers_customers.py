from rest_framework import serializers

from allauth.account import app_settings as allauth_settings
from allauth.account.utils import complete_signup

from astrosat.serializers import ContextVariableDefault

from astrosat_users.models import Customer, CustomerUser, User, UserRole

from .serializers_users import UserSerializerBasic
from .serializers_auth import RegisterSerializer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("id", "type", "name", "title", "description", "logo", "url", "country", "address", "postcode")

    id = serializers.UUIDField(read_only=True)
    type = serializers.CharField(source="customer_type")


class CustomerUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerUser
        fields = ("id", "type", "status", "user", "customer")

    type = serializers.CharField(source="customer_user_type", required=False)
    status = serializers.CharField(source="customer_user_status", required=False)

    customer = serializers.SlugRelatedField(
        default=ContextVariableDefault("customer", raise_error=True),
        queryset=Customer.objects.all(),
        slug_field="name",
        write_only=True,
    )
    user = (
        UserSerializerBasic()
    )  # note I don't use the full UserSerializer b/c I don't need to serialize the customer

    def update(self, instance, validated_data):
        user_serializer = self.fields["user"]
        user_data = validated_data.pop(user_serializer.source)
        user_serializer.update(instance.user, user_data)
        customer_user = super().update(instance, validated_data)
        return customer_user

    def create(self, validated_data):

        user_serializer = self.fields["user"]
        user_data = validated_data.pop(user_serializer.source).copy()

        try:
            user = User.objects.get(email=user_data["email"])
        except User.DoesNotExist:
            # new user, perform registration...
            default_password = User.objects.make_random_password()
            user_data.update({
                "change_password": True,
                "accepted_terms": True,
                "password1": default_password,
                "password2": default_password,
            })
            register_serializer = RegisterSerializer(data=user_data)
            if register_serializer.is_valid():
                request = self.context["request"]
                user = register_serializer.save(request)
                complete_signup(request, user, allauth_settings.EMAIL_VERIFICATION, None)
            # no else block is needed; UserSerializerBasic will catch any errors

        user_serializer.update(user, user_data)
        validated_data["user"] = user

        return super().create(validated_data)
