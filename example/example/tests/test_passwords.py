import pytest
import factory
import re

from django.core import mail
from django.core.exceptions import ValidationError
from django.urls import resolve, reverse

from rest_framework import status
from rest_framework.test import APIClient

from allauth.account.utils import user_pk_to_url_str, url_str_to_user_pk

from astrosat_users.conf import app_settings
from astrosat_users.utils import rest_encode_user_pk, rest_decode_user_pk
from astrosat_users.validators import LengthPasswordValidator, StrengthPasswordValidator

from astrosat.tests.utils import *
from astrosat_users.tests.utils import *

from .factories import *


@pytest.mark.django_db
class TestPasswordValidation:
    def test_password_length(self, user):

        validator = LengthPasswordValidator()

        # fails if too short...
        with pytest.raises(ValidationError):
            validator.validate(generate_password(length=4))
        # fails if too long...
        with pytest.raises(ValidationError):
            validator.validate(generate_password(length=256))
        # succeeds if just right...
        validator.validate(generate_password(length=20))

    def test_password_strength(self, user):

        validator = StrengthPasswordValidator(strength=2)

        # fails if too common...
        with pytest.raises(ValidationError):
            validator.validate("foobar", user=user)
        # fails if it is too weak...
        with pytest.raises(ValidationError):
            validator.validate("jkl;1234", user=user)
        # fails if too similar to user attributes
        with pytest.raises(ValidationError):
            user.name = generate_password()
            user.save()
            validator.validate(user.name, user=user)
        # succeeds if just right...
        validator.validate(generate_password(), user=user)


@pytest.mark.django_db
class TestApiPassword:
    def test_password_change(self, user):

        token, key = create_auth_token(user)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        url = reverse("rest_password_change")

        # successfully changes a valid password
        password = generate_password()
        data = {"new_password1": password, "new_password2": password}

        response = client.post(url, data)
        user.refresh_from_db()
        assert status.is_success(response.status_code)
        assert user.check_password(password)

        # correctly denies a non-matching password
        password1 = generate_password()
        password2 = shuffle_string(password1)
        data = {"new_password1": password1, "new_password2": password2}
        response = client.post(url, data)
        user.refresh_from_db()
        assert status.is_client_error(response.status_code)
        assert user.check_password(password)

        # correctly denies an invalid password
        data = {"new_password1": "foobar", "new_password2": "foobar"}
        response = client.post(url, data)
        user.refresh_from_db()
        assert status.is_client_error(response.status_code)
        assert user.check_password(password)

    def test_password_reset(self, user):

        token, key = create_auth_token(user)

        url = reverse("rest_password_reset")

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        valid_email = user.email
        invalid_email = shuffle_string(user.username
                                      ) + "@" + valid_email.split("@")[1]

        # an invalid email doesn't send email...
        response = client.post(url, {"email": invalid_email})
        assert status.is_success(response.status_code)
        assert len(mail.outbox) == 0

        # a valid email does send email...
        response = client.post(url, {"email": valid_email})
        assert status.is_success(response.status_code)
        assert len(mail.outbox) == 1

    def test_password_reset_sends_email(self, user):

        url = reverse("rest_password_reset")

        client = APIClient()

        response = client.post(url, {"email": user.email})
        assert status.is_success(response.status_code)

        token_generator = get_adapter().default_token_generator
        reset_url = app_settings.ACCOUNT_CONFIRM_PASSWORD_CLIENT_URL.format(
            key=token_generator.make_token(user), uid=rest_encode_user_pk(user)
        )

        email = mail.outbox[0]
        assert user.email in email.to
        assert reset_url in email.body

    def test_password_verify_reset(self, user):
        """
        tests that resetting the password via an email link works.
        (the email link should open a client page that eventually
        makes a post to the view being tested here.)
        """

        password = generate_password()
        token_key = get_adapter().default_token_generator.make_token(user)
        uid = rest_encode_user_pk(user)

        url = reverse("rest_password_reset_confirm")
        client = APIClient()

        invalid_data = {
            "new_password1": password,
            "new_password2": password,
            "uid": shuffle_string(uid),
            "token": shuffle_string(token_key),
        }

        valid_data = {
            "new_password1": password,
            "new_password2": password,
            "uid": uid,
            "token": token_key,
        }

        invalid_data = {
            "new_password1": password,
            "new_password2": password,
            "uid": shuffle_string(uid),
            "token": shuffle_string(token_key),
        }

        # passing invalid data doesn't change pwd...
        response = client.post(url, invalid_data)
        user.refresh_from_db()
        assert status.is_client_error(response.status_code)
        assert user.check_password(user.raw_password)

        # passing valid data does change pwd...
        response = client.post(url, valid_data)
        user.refresh_from_db()
        assert status.is_success(response.status_code)
        assert user.check_password(password)

    def test_password_verify_reset_returns_user(self, user):
        """
        tests that resetting the password returns UserSerializerLite
        in the response
        """

        password = generate_password()
        token_key = get_adapter().default_token_generator.make_token(user)
        uid = rest_encode_user_pk(user)

        url = reverse("rest_password_reset_confirm")
        client = APIClient()

        data = {
            "new_password1": password,
            "new_password2": password,
            "uid": uid,
            "token": token_key,
        }

        response = client.post(url, data)
        content = response.json()
        assert status.is_success(response.status_code)
        assert content["user"]["email"] == user.email
