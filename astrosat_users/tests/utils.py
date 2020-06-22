import pytest
from random import shuffle

from django.core.files.storage import get_storage_class

from factory.faker import Faker as FactoryFaker

from allauth.account.adapter import get_adapter

from dj_rest_auth.models import TokenModel
from dj_rest_auth.app_settings import TokenSerializer, create_token


##############
# useful fns #
##############


def shuffle_string(string):
    """
    Mixes up a string.
    Useful for generating invalid passwords, usernames, etc.
    """
    string_list = list(string)
    shuffle(string_list)
    return "".join(string_list)


def generate_password(**kwargs):
    """
    generates a password
    """
    password_kwargs = {
        "length": 20,
        "special_chars": True,
        "digits": True,
        "upper_case": True,
        "lower_case": True,
    }
    password_kwargs.update(kwargs)
    assert password_kwargs["length"] >= 4  # faker will break if the pwd is _too_ short
    password_faker = FactoryFaker("password", **password_kwargs)
    return password_faker.generate(extra_kwargs={})


##########################
# allauth-specific stuff #
##########################


def get_adapter_from_response(response):
    """
    Get the adapter being used by a particular test.
    """
    request = response.wsgi_request
    adapter = get_adapter(request)
    return adapter


def create_auth_token(user):
    """
    returns a knox token for a specific user.
    """
    return create_token(TokenModel, user, TokenSerializer)


#########
# mocks #
#########

# TODO: THIS FEELS LIKE IT SHOULD BE DEFINED ELSEWHERE
@pytest.fixture
def mock_storage(monkeypatch):
    """
    Mocks the backend storage system by not actually accessing media
    """
    def _mock_save(instance, name, content):
        setattr(instance, f"mock_{name}_exists", True)
        return str(name).replace("\\", "/")

    def _mock_delete(instance, name):
        setattr(instance, f"mock_{name}_exists", False)
        pass

    def _mock_exists(instance, name):
        return getattr(instance, f"mock_{name}_exists", False)

    storage_class = get_storage_class()
    monkeypatch.setattr(storage_class, "_save", _mock_save)
    monkeypatch.setattr(storage_class, "delete", _mock_delete)
    monkeypatch.setattr(storage_class, "exists", _mock_exists)
