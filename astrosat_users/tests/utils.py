from random import shuffle

from factory.faker import Faker as FactoryFaker

from allauth.account.adapter import get_adapter

from rest_auth.models import TokenModel
from rest_auth.app_settings import TokenSerializer, create_token


def get_adapter_from_response(response):
    """
    Get the adapter being used by a particular test.
    """
    request = response.wsgi_request
    adapter = get_adapter(request)
    return adapter


def shuffle_string(string):
    """
    Mixes up a string.
    Useful for generating invalid passwords, usernames, etc.
    """
    string_list = list(string)
    shuffle(string_list)
    return "".join(string_list)


def create_auth_token(user):
    """
    returns a knox token for a specific user.
    """
    return create_token(TokenModel, user, TokenSerializer)


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
