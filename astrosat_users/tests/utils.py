from faker import Faker

from allauth.account.adapter import get_adapter

from dj_rest_auth.models import TokenModel
from dj_rest_auth.app_settings import TokenSerializer, create_token

fake = Faker()

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
    return fake.password(**password_kwargs)


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
