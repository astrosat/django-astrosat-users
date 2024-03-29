from rest_framework import serializers

from allauth.account.adapter import get_adapter

from astrosat.serializers import ContextVariableDefault

from astrosat_users.models import Customer, CustomerUser, User, UserRole

from .serializers_users import UserSerializerBasic
from .serializers_auth import RegisterSerializer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = (
            "id",
            "type",
            "name",
            "official_name",
            "company_type",
            "registered_id",
            "vat_number",
            "description",
            "logo",
            "url",
            "country",
            "address",
            "postcode"
        )

    id = serializers.UUIDField(read_only=True)
    type = serializers.CharField(source="customer_type")

    def validate(self, data):
        # the client sometimes includes empty strings as data
        # these should be converted to None for some fields
        ignorable_fields = ["official_name", "registered_id"]
        for field_name in ignorable_fields:
            field_value = data.get(field_name)
            if field_value is not None and not field_value:
                data[field_name] = None
        return data


class CustomerUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerUser
        fields = ("id", "type", "status", "invitation_date", "user", "customer")

    type = serializers.CharField(source="customer_user_type", required=False)
    status = serializers.CharField(
        source="customer_user_status", required=False
    )
    invitation_date = serializers.DateTimeField(read_only=True)

    customer = serializers.SlugRelatedField(
        default=ContextVariableDefault("customer", raise_error=True),
        queryset=Customer.objects.all(),
        slug_field="name",
        write_only=True,
    )
    user = (
        UserSerializerBasic()
    )  # note I don't use the full UserSerializer b/c I don't need to serialize the customer

    def validate(self, data):
        if not self.instance:
            customer = data["customer"]
            user_email = data["user"]["email"]
            if customer.users.filter(email=user_email).exists():
                raise serializers.ValidationError(
                    "User is already a member of Customer."
                )

        return data

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
                "accepted_terms": True,
                # accepted_terms must be True for registration to succeed
                # (assuming UserSettings.require_terms_acceptance is True)
                # but I want a newly-created user to have to explicitly accept terms
                # so I update the value immediately after calling is_valid below
                "change_password": True,
                "password1": default_password,
                "password2": default_password,
            })
            register_serializer = RegisterSerializer(data=user_data)
            if register_serializer.is_valid():
                user_data.pop("accepted_terms")
                register_serializer.validated_data["accepted_terms"] = False
                user = register_serializer.save(self.context["request"])
            # no else block is needed; UserSerializerBasic will catch any errors

        user_serializer.update(user, user_data)
        validated_data["user"] = user

        return super().create(validated_data)
