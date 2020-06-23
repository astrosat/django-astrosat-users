from django.urls import resolve, reverse

import pytest
import factory

from rest_framework import status
from rest_framework.test import APIClient

# (these next 3 variables are imported internaly from "settings.py")
from dj_rest_auth.models import TokenModel
from dj_rest_auth.app_settings import TokenSerializer, create_token

from astrosat.tests.utils import *
from astrosat_users.tests.utils import *
from astrosat_users.utils import rest_encode_user_pk, rest_decode_user_pk

from .factories import *


@pytest.mark.django_db
def test_user_encoding_and_decoding(user):
    encoded_uid = rest_encode_user_pk(user)
    decoded_uid = rest_decode_user_pk(encoded_uid)
    assert encoded_uid != str(user.pk)
    assert decoded_uid == str(user.pk)


@pytest.mark.django_db
class TestTokens:
    """
    tests that TokenAuthentication works via the API
    """

    def test_get_token(self, user, user_settings):

        user_settings.require_approval = False
        user_settings.require_verification = False
        user_settings.save()

        assert user.auth_token_set.count() == 0

        test_data = {"email": user.email, "password": user.raw_password}

        client = APIClient()
        response = client.post(reverse("rest_login"), test_data)
        data = response.json()

        assert status.is_success(response.status_code)
        assert set(data.keys()) == set(["user", "token"])

        user.refresh_from_db()
        assert user.auth_token_set.count() == 1

    def test_use_token(self, user):

        token, key = create_auth_token(user)
        invalid_key = shuffle_string(key)

        client = APIClient()
        url = reverse("users-list")  # an authenticated view to test w/

        client.credentials()
        response = client.get(url)
        assert status.is_client_error(response.status_code)

        client.credentials(HTTP_AUTHORIZATION=f"Token {invalid_key}")
        response = client.get(url)
        assert status.is_client_error(response.status_code)

        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        response = client.get(url)
        assert status.is_success(response.status_code)

    def test_deleted_token(self, user):
        """
        tests that logging in w/ a token that is no longer in the db fails
        """

        token, key = create_auth_token(user)

        client = APIClient()
        url = reverse("users-list")  # an authenticated view to test w/

        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        response = client.get(url)
        assert status.is_success(response.status_code)

        token.delete()
        response = client.get(url)
        assert status.is_client_error(response.status_code)
        assert response.json()["detail"].lower() == "invalid token."

    # def test_expired_token(self, user):
    #     raise NotImplementedError()
