from rest_framework import serializers

from astrosat_users.models import Customer, CustomerUser
from astrosat_users.serializers import UserSerializer


# TODO: MAKE THESE NESTED WRITABLE


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("type", "name", "title", "description", "logo", "url")

    type = serializers.CharField(source="customer_type")


class CustomerUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerUser
        fields = (
            "type",
            "status",
            # "user",
            "details",
        )

    type = serializers.CharField(source="customer_user_type")
    status = serializers.CharField(source="customer_user_status")
    # user = serializers.SlugRelatedField(read_only=True, slug_field="email")
    details = UserSerializer(source="user", many=False)
