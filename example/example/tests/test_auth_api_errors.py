from django.urls import reverse

import pytest

from rest_framework import status
from rest_framework.test import APIClient

from astrosat.tests.utils import *
from astrosat_users.tests.utils import *
from astrosat_users.utils import rest_decode_user_pk, rest_encode_user_pk

from .factories import *


NON_FIELD_ERRORS_KEY = "non_field_errors"


@pytest.mark.django_db
class TestRegistrationErrors:

    """
    Make sure all the errors to do w/ registration are as expected
    """

    url = reverse("rest_register")

    def test_registration_closed(self, user_data, user_settings):

        user_settings.allow_registration = False
        user_settings.save()

        client = APIClient()

        test_data = {
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
        }

        # NOTE THAT THIS IS ACTUALLY A PERMISSIONS ERROR AND NOT A SERIALIZER ERROR
        CLOSED_REGISTRATION_ERROR_RESPONSE = {
            "detail": "We are sorry, but the sign up is currently closed."
        }

        response = client.post(self.url, test_data)
        assert status.is_client_error(response.status_code)
        assert response.json() == CLOSED_REGISTRATION_ERROR_RESPONSE

    def test_unaccepted_terms(self, user_data, user_settings):

        user_settings.allow_registration = True
        user_settings.require_terms_acceptance = True
        user_settings.save()

        client = APIClient()

        test_data = {
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
            "accepted_terms": False,
        }

        UNNACCEPTED_TERMS_ERROR_RESPONSE = {
            "errors": {"accepted_terms": ["Accepting terms & conditions is required."]}
        }

        response = client.post(self.url, test_data)
        assert status.is_client_error(response.status_code)
        assert response.json() == UNNACCEPTED_TERMS_ERROR_RESPONSE

    def test_invalid_password(self, user_data):

        client = APIClient()

        test_data = {
            "email": user_data["email"],
            "password1": "password",
            "password2": "password",
        }

        INVALID_PASSWORD_ERROR_RESPONSE = {
            "errors": {
                "password1": [
                    "The password must not be weak."
                ]
            }
        }

        response = client.post(self.url, test_data)
        assert status.is_client_error(response.status_code)
        assert response.json() == INVALID_PASSWORD_ERROR_RESPONSE

    def test_non_matching_password(self, user_data):

        client = APIClient()

        test_data = {
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": shuffle_string(user_data["password"]),
        }

        NON_MATCHING_PASSWORD_ERROR_RESPONSE = {
            "errors": {NON_FIELD_ERRORS_KEY: ["The two password fields didn't match."]}
        }

        response = client.post(self.url, test_data)
        assert status.is_client_error(response.status_code)
        assert response.json() == NON_MATCHING_PASSWORD_ERROR_RESPONSE

    def test_existing_user(self, user, mock_storage):

        client = APIClient()

        user = UserFactory()
        test_data = {
            "email": user.email,
            "password1": user.raw_password,
            "password2": user.raw_password,
        }

        EXISTING_USER_ERROR_RESPONSE = {
            "errors": {
                "email": ["A user is already registered with this e-mail address."]
            }
        }

        response = client.post(self.url, test_data)
        assert status.is_client_error(response.status_code)
        assert response.json() == EXISTING_USER_ERROR_RESPONSE

    def test_missing_field(self, user_data):

        client = APIClient()

        test_data = {"email": user_data["email"], "password1": user_data["password"]}

        MISSING_FIELD_ERROR_RESPONSE = {
            "errors": {"password2": ["This field is required."]}
        }

        response = client.post(self.url, test_data)
        assert status.is_client_error(response.status_code)
        assert response.json() == MISSING_FIELD_ERROR_RESPONSE


@pytest.mark.django_db
class TestLoginErrors:

    url = reverse("rest_login")

    def test_unknown_user(self, user_data):

        client = APIClient()

        test_data = {"email": user_data["email"], "password": user_data["password"]}

        UNKNOWN_USER_ERROR_RESPONSE = {
            "errors": {
                NON_FIELD_ERRORS_KEY: ["Unable to log in with provided credentials."]
            }
        }

        response = client.post(self.url, test_data)
        assert status.is_client_error(response.status_code)
        assert response.json() == UNKNOWN_USER_ERROR_RESPONSE

    def test_incorrect_password(self, user):

        client = APIClient()

        test_data = {"email": user.email, "password": shuffle_string(user.raw_password)}

        INCORRECT_PASSWORD_ERROR_RESPONSE = {
            "errors": {
                NON_FIELD_ERRORS_KEY: ["Unable to log in with provided credentials."]
            }
        }

        response = client.post(self.url, test_data)
        assert status.is_client_error(response.status_code)
        assert response.json() == INCORRECT_PASSWORD_ERROR_RESPONSE

    def test_missing_field(self, user):

        client = APIClient()

        test_data = {"email": user.email}

        MISSING_FIELD_ERROR_RESPONSE = {
            "errors": {"password": ["This field is required."]}
        }

        response = client.post(self.url, test_data)
        assert status.is_client_error(response.status_code)
        assert response.json() == MISSING_FIELD_ERROR_RESPONSE

    def test_inactive_user(self, user_settings, mock_storage):

        client = APIClient()

        user_settings.allow_registration = True
        user_settings.require_approval = False
        user_settings.require_verification = False
        user_settings.require_terms_acceptance = False
        user_settings.save()

        user = UserFactory(is_active=False)
        test_data = {"email": user.email, "password": user.raw_password}

        # TODO: THOUGHT THIS WOULD RETURN "User account is disabled."
        # TODO: BUT LOW-LEVEL DJANGO-NESS: https://github.com/pennersr/django-allauth/blob/b52a61b4d5c74c586f032c761cd0f902df20fd4b/allauth/account/auth_backends.py#L62
        INACTIVE_USER_ERROR_RESPONSE = {
            "errors": {
                NON_FIELD_ERRORS_KEY: ["Unable to log in with provided credentials."]
            }
        }

        response = client.post(self.url, test_data)
        assert status.is_client_error(response.status_code)
        assert response.json() == INACTIVE_USER_ERROR_RESPONSE

    def test_unverified_user(self, user_settings, mock_storage):

        client = APIClient()

        user_settings.allow_registration = True
        user_settings.require_approval = False
        user_settings.require_verification = True
        user_settings.require_terms_acceptance = False
        user_settings.save()

        user = UserFactory()
        assert not user.is_verified

        test_data = {"email": user.email, "password": user.raw_password}

        UNVERIFIED_USER_ERROR_RESPONSE = {
            "errors": {NON_FIELD_ERRORS_KEY: [f"User {user} is not verified."]}
        }

        response = client.post(self.url, test_data)
        assert status.is_client_error(response.status_code)
        # UNVERIFIED_USER_ERROR_RESPONSE is only a subset of the response
        assert UNVERIFIED_USER_ERROR_RESPONSE.items() <= response.json().items()

    def test_unapproved_user(self, user_settings, mock_storage):

        client = APIClient()

        user_settings.allow_registration = True
        user_settings.require_approval = True
        user_settings.require_verification = False
        user_settings.require_terms_acceptance = False
        user_settings.save()

        user = UserFactory(is_approved=False)
        assert not user.is_approved

        test_data = {"email": user.email, "password": user.raw_password}

        UNAPPROVED_USER_ERROR_RESPONSE = {
            "errors": {NON_FIELD_ERRORS_KEY: [f"User {user} has not been approved."]}
        }

        response = client.post(self.url, test_data)
        assert status.is_client_error(response.status_code)
        # UNAPPROVED_USER_ERROR_RESPONSE is only a subset of the response
        assert UNAPPROVED_USER_ERROR_RESPONSE.items() <= response.json().items()

    def test_unaccepted_user(self, user_settings, mock_storage):

        client = APIClient()

        user_settings.allow_registration = True
        user_settings.require_approval = False
        user_settings.require_verification = False
        user_settings.require_terms_acceptance = True
        user_settings.save()

        user = UserFactory(accepted_terms=False)
        assert not user.accepted_terms

        test_data = {"email": user.email, "password": user.raw_password}

        UNACCEPTED_USER_ERROR_RESPONSE = {
            "errors": {
                NON_FIELD_ERRORS_KEY: [
                    f"User {user} has not yet accepted the terms & conditions."
                ]
            }
        }

        response = client.post(self.url, test_data)
        assert status.is_client_error(response.status_code)
        # UNACCEPTED_USER_ERROR_RESPONSE is only a subset of the response
        assert UNACCEPTED_USER_ERROR_RESPONSE.items() <= response.json().items()


@pytest.mark.django_db
class TestLogoutErrors:

    url = reverse("rest_logout")

    def test_not_authenticated(self, user):

        client = APIClient()

        NOT_AUTHENTICATED_ERROR_RESPONSE = {
            "detail": "Authentication credentials were not provided."
        }

        response = client.post(self.url)
        assert status.is_client_error(response.status_code)
        assert response.json() == NOT_AUTHENTICATED_ERROR_RESPONSE


@pytest.mark.django_db
class TestPasswordErrors:

    change_url = reverse("rest_password_change")
    reset_url = reverse("rest_password_reset")
    reset_confirm_url = reverse("rest_password_reset_confirm")

    ################
    # change views #
    ################

    def test_non_matching_password(self, user):

        _, key = create_auth_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        test_data = {
            "new_password1": user.raw_password,
            "new_password2": shuffle_string(user.raw_password),
        }

        # TODO: THERE IS AN INCONSISTENCY IN DJANGO!  ("didn’t" instead of "didn't") BAD BAD DJANGO!
        # TODO: https://github.com/django/django/blob/505fec6badba0622bbf97bb659188c3d62a9bc58/django/contrib/auth/forms.py#L334
        NON_MATCHING_PASSWORD_ERROR_RESPONSE = {
            "errors": {"new_password2": ["The two password fields didn’t match."]}
        }

        response = client.post(self.change_url, test_data)
        assert status.is_client_error(response.status_code)
        assert response.json() == NON_MATCHING_PASSWORD_ERROR_RESPONSE

    def test_missing_field(self, user):

        _, key = create_auth_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        test_data = {"new_password1": user.raw_password}

        MISSING_FIELD_ERROR_RESPONSE = {
            "errors": {"new_password2": ["This field is required."]}
        }

        response = client.post(self.change_url, test_data)
        assert status.is_client_error(response.status_code)
        assert response.json() == MISSING_FIELD_ERROR_RESPONSE

    def test_invalid_password(self, user):

        _, key = create_auth_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        test_data = {"new_password1": "password", "new_password2": "password"}

        INVALID_PASSWORD_ERROR_RESPONSE = {
            "errors": {
                "new_password2": [
                    "The password must not be weak."
                ]
            }
        }

        response = client.post(self.change_url, test_data)
        assert status.is_client_error(response.status_code)
        assert response.json() == INVALID_PASSWORD_ERROR_RESPONSE

    ###############
    # reset views #
    ###############

    def test_reset_unknown_user(self, user_data):

        client = APIClient()

        test_data = {"email": user_data["email"]}

        UNKNOWN_USER_ERROR_RESPONSE = {
            "errors": {
                "email": ["The e-mail address is not assigned to any user account"]
            }
        }

        response = client.post(self.reset_url, test_data)
        assert status.is_client_error(response.status_code)
        assert response.json() == UNKNOWN_USER_ERROR_RESPONSE

    #######################
    # reset confirm views #
    #######################

    def test_confirm_invalid_password(self, user):

        client = APIClient()

        uid = rest_encode_user_pk(user)
        token_key = get_adapter().default_token_generator.make_token(user)

        test_data = {
            "new_password1": "password",
            "new_password2": "password",
            "uid": uid,
            "token": token_key,
        }

        INVALID_PASSWORD_ERROR_RESPONSE = {
            "errors": {
                "new_password2": [
                    "The password must not be weak."
                ]
            }
        }

        response = client.post(self.reset_confirm_url, test_data)
        assert status.is_client_error(response.status_code)
        assert response.json() == INVALID_PASSWORD_ERROR_RESPONSE

    def test_confirm_invalid_key(self, user):

        client = APIClient()

        password = generate_password()
        token_key = get_adapter().default_token_generator.make_token(user)
        uid = rest_encode_user_pk(user)

        test_data = {
            "new_password1": password,
            "new_password2": password,
            "uid": uid,
            "token": shuffle_string(token_key),
        }

        INVALID_KEY_ERROR_RESPONSE = {"errors": {"token": ["The link is broken or expired."]}}

        response = client.post(self.reset_confirm_url, test_data)
        assert status.is_client_error(response.status_code)
        assert response.json() == INVALID_KEY_ERROR_RESPONSE


@pytest.mark.django_db
class TestEmailErrors:
    """
    Make sure all the errors to do w/ verifying a user's email are as expected
    """

    send_email_verifciation_url = reverse("rest_send_email_verification")
    verify_email_url = reverse("rest_verify_email")

    #################################
    # send verification email views #
    #################################

    def test_unknown_user(self, user_data):

        client = APIClient()

        test_data = {"email": user_data["email"]}

        UNKNOWN_USER_ERROR_RESPONSE = {
            "errors": {
                NON_FIELD_ERRORS_KEY: [
                    f"Unable to find user with '{test_data['email']}' address."
                ]
            }
        }

        response = client.post(self.send_email_verifciation_url, test_data)
        assert status.is_client_error(response.status_code)
        assert response.json() == UNKNOWN_USER_ERROR_RESPONSE

    ##############################
    # perform verification views #
    ##############################

    def test_missing_key(self, user):

        client = APIClient()

        test_data = {}

        MISSING_KEY_ERROR_RESPONSE = {"errors": {"key": ["This field is required."]}}

        response = client.post(self.verify_email_url, test_data)
        assert status.is_client_error(response.status_code)
        assert response.json() == MISSING_KEY_ERROR_RESPONSE

    def test_invalid_key(self, user):

        client = APIClient()

        test_data = {"key": "invalid_key"}

        INVALID_KEY_ERROR_RESPONSE = {
            "errors": {NON_FIELD_ERRORS_KEY: ["This is an invalid key."]}
        }

        response = client.post(self.verify_email_url, test_data)
        assert status.is_client_error(response.status_code)
        assert response.json() == INVALID_KEY_ERROR_RESPONSE
