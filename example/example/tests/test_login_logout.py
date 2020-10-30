import pytest

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.test import Client
from django.urls import resolve, reverse

from rest_framework import status
from rest_framework.settings import api_settings as drf_settings
from rest_framework.test import APIClient

from astrosat.tests.utils import *

from astrosat_users.conf import app_settings
from astrosat_users.tests.utils import create_auth_token

from .factories import *


@pytest.mark.django_db
class TestAPILoginLogout:

    CHANGE_PASSWORD_MSG = "A password reset email has been sent."
    INVALID_METHOD_MSG = 'Method "{}" not allowed.'
    INVALID_TOKEN_MSG = "Invalid token."
    INACTIVE_USER_MSG = "Unable to log in with provided credentials."
    SUCCESSFUL_LOGOUT_MSG = "Successfully logged out."
    UNACCEPTED_TERMS = "User {} has not yet accepted the terms & conditions."
    UNAPPROVED_MSG = "User {} has not been approved."
    UNAUTHENTICATED_MSG = "Authentication credentials were not provided."
    UNVERIFIED_MSG = "User {} is not verified."

    login_url = reverse("rest_login")
    logout_url = reverse("rest_logout")

    def login(self, *args, **kwargs):
        """
        convenience fn for logging into the client
        """
        client = kwargs.get("client", APIClient())
        url = kwargs.get("url", self.login_url)
        user = kwargs.get("user", UserFactory())
        data = {"email": user.email, "password": user.raw_password}
        if "accepted_terms" in kwargs:
            data["accepted_terms"] = kwargs.get("accepted_terms")
        response = client.post(url, data)
        return response

    def test_login_inactive(self, user, user_settings):

        user.accepted_terms = True
        user.is_approved = True
        user.is_active = False
        user.verify()
        user.save()

        response = self.login(user=user)
        content = response.json()
        assert status.is_client_error(response.status_code)
        assert content["errors"] == {
            drf_settings.NON_FIELD_ERRORS_KEY: [self.INACTIVE_USER_MSG]
        }

        request_user = response.wsgi_request.user
        assert request_user != user and not request_user.is_authenticated

    def test_login_unverified(self, user, user_settings):

        assert user_settings.require_verification is True
        assert user.is_verified is False

        response = self.login(user=user)
        content = response.json()
        assert status.is_client_error(response.status_code)
        assert content["errors"] == {
            drf_settings.NON_FIELD_ERRORS_KEY: [self.UNVERIFIED_MSG.format(user)]
        }

        request_user = response.wsgi_request.user
        assert request_user != user and not request_user.is_authenticated

        user.verify()

        response = self.login(user=user)
        content = response.json()
        assert status.is_success(response.status_code)
        assert content["user"]["is_verified"] == True

        request_user = response.wsgi_request.user
        assert request_user == user

    def test_login_unapproved(self, user, user_settings):

        user_settings.require_verification = False
        user_settings.require_approval = True
        user_settings.require_terms_acceptance = False
        user_settings.save()

        assert user.is_approved is False

        response = self.login(user=user)
        content = response.json()
        assert status.is_client_error(response.status_code)
        assert content["errors"] == {
            drf_settings.NON_FIELD_ERRORS_KEY: [self.UNAPPROVED_MSG.format(user)]
        }

        request_user = response.wsgi_request.user
        assert request_user != user and not request_user.is_authenticated

        user.is_approved = True
        user.save()

        response = self.login(user=user)
        content = response.json()
        assert status.is_success(response.status_code)
        assert content["user"]["is_approved"] == True

        request_user = response.wsgi_request.user
        assert request_user == user

    def test_login_unaccepted(self, user, user_settings):

        user_settings.require_verification = False
        user_settings.require_approval = False
        user_settings.require_terms_acceptance = True
        user_settings.save()

        user.accepted_terms = False
        user.save()

        response = self.login(user=user)
        content = response.json()
        assert status.is_client_error(response.status_code)
        assert content["errors"] == {
            drf_settings.NON_FIELD_ERRORS_KEY: [self.UNACCEPTED_TERMS.format(user)]
        }

        request_user = response.wsgi_request.user
        assert request_user != user and not request_user.is_authenticated

        user.accepted_terms = True
        user.save()

        response = self.login(user=user)
        content = response.json()
        assert status.is_success(response.status_code)
        assert content["user"]["accepted_terms"] == True

        request_user = response.wsgi_request.user
        assert request_user == user

    def test_login_accepted(self, user, user_settings):
        """
        tests that I can manipulate accepted_terms via login
        """

        user_settings.require_verification = False
        user_settings.require_approval = False
        user_settings.require_terms_acceptance = True
        user_settings.save()

        user.accepted_terms = False
        user.save()

        response = self.login(user=user, accepted_terms=True)
        content = response.json()

        assert status.is_success(response.status_code)
        assert content["user"]["accepted_terms"] == True

        request_user = response.wsgi_request.user
        assert request_user == user

        response = self.login(user=user, accepted_terms=False)
        content = response.json()

        assert status.is_client_error(response.status_code)
        assert content["errors"] == {
            drf_settings.NON_FIELD_ERRORS_KEY: [self.UNACCEPTED_TERMS.format(user)]
        }

        request_user = response.wsgi_request.user
        assert request_user != user and not request_user.is_authenticated

    def test_login_change_password(self, user, user_settings):

        user_settings.require_verification = False
        user_settings.require_approval = False
        user_settings.require_terms_acceptance = False
        user_settings.save()

        user.change_password = True
        user.save()

        assert len(mail.outbox) == 0

        response = self.login(user=user)
        content = response.json()
        assert status.is_client_error(response.status_code)
        assert content["errors"] == {
            drf_settings.NON_FIELD_ERRORS_KEY: [self.CHANGE_PASSWORD_MSG]
        }

        request_user = response.wsgi_request.user
        assert request_user != user and not request_user.is_authenticated

        assert len(mail.outbox) == 1
        assert user.email in mail.outbox[0].to

        user.change_password = False
        user.save()

        response = self.login(user=user)
        content = response.json()
        assert status.is_success(response.status_code)
        assert content["user"]["change_password"] == False

        request_user = response.wsgi_request.user
        assert request_user == user

    def test_logout(self, user):

        token, key = create_auth_token(user)

        client = APIClient()
        self.login(client=client, user=user)

        # make sure I can't logout w/out a token
        response = client.post(self.logout_url)
        content = response.json()
        assert status.is_client_error(response.status_code)
        assert content["detail"] == self.UNAUTHENTICATED_MSG

        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        # make sure I can't logout via a GET
        response = client.get(self.logout_url)
        content = response.json()
        assert status.is_client_error(response.status_code)
        assert content["detail"] == self.INVALID_METHOD_MSG.format("GET")

        # make sure I can logout w/ a valid token
        response = client.post(self.logout_url)
        content = response.json()
        assert status.is_success(response.status_code)
        assert content["detail"] == self.SUCCESSFUL_LOGOUT_MSG
        request_user = response.wsgi_request.user
        assert isinstance(request_user, AnonymousUser)

    def test_logout_all(self, user):

        token, key = create_auth_token(user)
        url = reverse("users-list")  # an authenticated view to test w/

        client = APIClient()
        self.login(client=client, user=user)

        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        # I _can_ access the page prior to calling `.logout_all()`
        response = client.get(url)
        assert status.is_success(response.status_code)

        user.logout_all()

        # I _cannot_ access the page after calling `.logout_all()`
        response = client.get(url)
        assert status.is_client_error(response.status_code)
        assert response.json()["detail"] == self.INVALID_TOKEN_MSG


@pytest.mark.django_db
class TestBackendLoginLogout:

    login_url = reverse("account_login")
    logout_url = reverse("account_logout")

    def login(self, *args, **kwargs):
        """
        convenience fn for logging into the client
        """
        client = kwargs.get("client", Client(enforce_csrf_checks=False))
        url = kwargs.get("url", self.login_url)
        user = kwargs.get("user", UserFactory())
        data = {"login": user.email, "password": user.raw_password}
        response = client.post(url, data)
        return response

    def test_login_inactive(self, user, user_settings):

        user.accepted_terms = True
        user.is_approved = True
        user.is_active = False
        user.verify()
        user.save()

        response = self.login(user=user)
        assert status.is_redirect(response.status_code)

        request_user = response.wsgi_request.user
        assert request_user != user and not request_user.is_authenticated

        assert resolve(response.url).view_name == "account_inactive"

    def test_login_unverified(self, user, user_settings):

        assert user_settings.require_verification is True
        assert user.is_verified is False

        # an unverified user cannot login...
        response = self.login(user=user)
        assert status.is_redirect(response.status_code)

        request_user = response.wsgi_request.user
        assert request_user != user and not request_user.is_authenticated

        assert resolve(response.url).view_name == "account_email_verification_sent"

        # a verified user can login...
        user.verify()
        response = self.login(user=user)
        assert status.is_redirect(response.status_code)

        request_user = response.wsgi_request.user
        assert request_user == user and user.is_authenticated

        assert response.url == settings.LOGIN_REDIRECT_URL

    def test_login_unapproved(self, user, user_settings):

        user_settings.require_verification = False
        user_settings.require_approval = True
        user_settings.save()

        user.is_approved = False
        user.save()

        # an unapproved user can't login...

        response = self.login(user=user)
        request_user = response.wsgi_request.user
        assert request_user != user and not request_user.is_authenticated

        # an approved user can login...

        user.is_approved = True
        user.save()

        response = self.login(user=user)
        assert status.is_redirect(response.status_code)

        request_user = response.wsgi_request.user
        assert request_user == user and user.is_authenticated

        assert response.url == settings.LOGIN_REDIRECT_URL

    def test_login_unaccepted(self, user, user_settings):

        user_settings.require_verification = False
        user_settings.require_approval = False
        user_settings.require_terms_acceptance = True
        user_settings.save()

        user.accepted_terms = False
        user.save()

        # an unaccepted user can't login...

        response = self.login(user=user)
        request_user = response.wsgi_request.user
        assert request_user != user and not request_user.is_authenticated

        # an accepted user can login...

        user.accepted_terms = True
        user.save()

        response = self.login(user=user)
        assert status.is_redirect(response.status_code)

        request_user = response.wsgi_request.user
        assert request_user == user and user.is_authenticated

        assert response.url == settings.LOGIN_REDIRECT_URL

    def test_login_change_password(self, user, user_settings):

        user_settings.require_verification = False
        user_settings.require_approval = False
        user_settings.require_terms_acceptance = False
        user_settings.save()

        user.change_password = True
        user.save()

        assert len(mail.outbox) == 0

        response = self.login(user=user)

        assert status.is_redirect(response.status_code)
        assert resolve(response.url).view_name == "account_reset_password_done"

        request_user = response.wsgi_request.user
        assert isinstance(request_user, AnonymousUser)

        assert len(mail.outbox) == 1
        assert user.email in mail.outbox[0].to

        user.change_password = False
        user.save()

        response = self.login(user=user)
        assert status.is_redirect(response.status_code)

        request_user = response.wsgi_request.user
        assert request_user == user and user.is_authenticated

        assert response.url == settings.LOGIN_REDIRECT_URL

    def test_logout(self, user):

        client = Client()
        client.force_login(user)

        # make sure I can't logout via a GET
        response = client.get(self.logout_url)
        request_user = response.wsgi_request.user

        assert status.is_success(response.status_code)
        assert request_user == user and request_user.is_authenticated

        # make sure I _can_ logout w/ a token via a POST
        response = client.post(self.logout_url)
        request_user = response.wsgi_request.user
        assert status.is_redirect(response.status_code)
        assert request_user != user and not request_user.is_authenticated
        assert response.url == settings.LOGOUT_REDIRECT_URL
