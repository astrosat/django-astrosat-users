import pytest
import factory
from factory.faker import (
    Faker as FactoryFaker,
)  # note I use FactoryBoy's wrapper of Faker
from django.test import Client

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from django.test import Client
from rest_framework.test import APIClient

from astrosat_users.models import UserSettings
from astrosat_users.serializers import UserSerializer

from .factories import UserFactory


@pytest.fixture
def user_data():
    """
    Provides a dictionary of user data.
    """

    # rather than use `.build()`, I actually create and then delete the model
    # this is so that the related profile can be created as well

    user = UserFactory()
    serializer = UserSerializer(user)
    data = serializer.data
    data["password"] = user.raw_password

    user.delete()

    # TODO: overwrite any supplied data...

    return data


@pytest.fixture
def user():
    user = UserFactory()
    # user.verify()
    return user


@pytest.fixture
def client():
    """
    a client to use w/ the backend
    """
    client = Client(enforce_csrf_checks=False)
    client.force_login(AnonymousUser())
    return client


@pytest.fixture
def api_client(user):
    """
    a client to use w/ the API
    """
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def user_settings():
    user_settings = UserSettings.load()
    return user_settings
