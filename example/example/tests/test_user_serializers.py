import pytest
import json

from astrosat_users.serializers import UserSerializer
from astrosat_users.tests.factories import CustomerFactory
from astrosat_users.tests.utils import *

from .factories import *


@pytest.mark.django_db
class TestUserSerializer:
    def test_serialize_user(self, mock_storage):

        # create a user that is a manager of some customer
        # with some roles and permissions
        user = UserFactory()
        customer = CustomerFactory()
        customer.add_user(user, type="MANAGER")

        serializer = UserSerializer(user)

        # mostly checking the non-obvious things (profiles, roles, permissions, customers)
        serializer_data = serializer.data
        assert serializer_data["email"] == user.email
        assert "example_profile" in serializer_data["profiles"]
        # roles
        # permissions
        assert serializer_data["customers"] == [
            {"type": "MANAGER", "status": "PENDING", "name": customer.name}
        ]
