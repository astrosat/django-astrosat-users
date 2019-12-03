import pytest
import factory

from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import Client
from django.urls import resolve, reverse

from allauth.utils import build_absolute_uri

from rest_framework import status
from rest_framework.test import APIClient

from astrosat_users.conf import app_settings
from astrosat_users.tests.utils import *

from .factories import *


@pytest.mark.django_db
class TestApiLoginLogout:

    UNAUTHENTICATED_MSG = "Authentication credentials were not provided."
    INVALID_METHOD_MSG = 'Method "{}" not allowed.'
    SUCCESSFUL_LOGOUT_MSG = "Successfully logged out."
    INVALID_TOKEN_MSG = "Invalid token."

    def login(self, *args, **kwargs):
        """
        convenience fn for logging into the client
        """
        client = kwargs.get("client", APIClient())
        url = kwargs.get("url", reverse("rest_login"))
        user = kwargs.get("user", UserFactory())
        data = {"email": user.email, "password": user.raw_password}
        response = client.post(url, data)
        return response

    def test_login_inactive(self, user, user_settings):

        user.verify()
        user.is_approved = True
        user.is_active = False
        user.save()

        response = self.login(user=user)
        assert status.is_client_error(response.status_code)

        request_user = response.wsgi_request.user
        assert request_user != user and not request_user.is_authenticated

    def test_login_unverified(self, user, user_settings):

        assert user_settings.require_verification is True
        assert user.is_verified is False

        response = self.login(user=user)
        assert status.is_client_error(response.status_code)

        request_user = response.wsgi_request.user
        assert request_user != user and not request_user.is_authenticated

        user.verify()

        response = self.login(user=user)
        assert status.is_success(response.status_code)

        request_user = response.wsgi_request.user
        assert request_user == user
        data = response.json()
        assert data["user"]["is_verified"] is True

    def test_login_unapproved(self, user, user_settings):

        user_settings.require_verification = False
        user_settings.require_approval = True
        user_settings.save()
        assert user.is_approved is False

        response = self.login(user=user)
        assert status.is_client_error(response.status_code)

        request_user = response.wsgi_request.user
        assert request_user != user and not request_user.is_authenticated

        user.is_approved = True
        user.save()

        response = self.login(user=user)
        assert status.is_success(response.status_code)

        request_user = response.wsgi_request.user
        assert request_user == user
        data = response.json()
        assert data["user"]["is_approved"] is True

    def test_logout(self, user):

        token, key = create_auth_token(user)
        url = reverse("rest_logout")

        client = APIClient()
        self.login(client=client, user=user)

        # make sure I can't logout w/out a token
        response = client.post(url)
        assert status.is_client_error(response.status_code)
        assert response.json()["detail"] == self.UNAUTHENTICATED_MSG

        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        # make sure I can't logout via a GET
        response = client.get(url)
        assert status.is_client_error(response.status_code)
        assert response.json()["detail"] == self.INVALID_METHOD_MSG.format("GET")

        # make sure I _can_ logout w/ a token via a POST
        response = client.post(url)
        assert status.is_success(response.status_code)
        assert response.json()["detail"] == self.SUCCESSFUL_LOGOUT_MSG

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
    def login(self, *args, **kwargs):
        """
        convenience fn for logging into the client
        """
        client = kwargs.get("client", Client(enforce_csrf_checks=False))
        url = kwargs.get("url", reverse("account_login"))
        user = kwargs.get("user", UserFactory())
        data = {"login": user.email, "password": user.raw_password}
        response = client.post(url, data)
        return response

    def test_login_inactive(self, user, user_settings):

        user.verify()
        user.is_approved = True
        user.is_active = False
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
        request_user = response.wsgi_request.user
        assert status.is_redirect(response.status_code)
        assert request_user != user and not request_user.is_authenticated
        assert resolve(response.url).view_name == "account_email_verification_sent"

        # a verified user can login...
        user.verify()
        response = self.login(user=user)
        request_user = response.wsgi_request.user
        assert status.is_redirect(response.status_code)
        assert request_user == user and user.is_authenticated
        assert response.url == get_adapter().get_login_redirect_url(
            response.wsgi_request
        )

    def test_login_unapproved(self, user, user_settings):

        user_settings.require_verification = False
        user_settings.require_approval = True
        user_settings.save()
        assert user.is_approved is False

        response = self.login(user=user)
        # an unapproved user can't login...
        request_user = response.wsgi_request.user
        assert status.is_redirect(response.status_code)
        assert request_user != user and not request_user.is_authenticated
        assert resolve(response.url).view_name == "disapproved"

        user.is_approved = True
        user.save()

        response = self.login(user=user)
        request_user = response.wsgi_request.user
        assert status.is_redirect(response.status_code)
        assert request_user == user and user.is_authenticated
        assert response.url == get_adapter().get_login_redirect_url(
            response.wsgi_request
        )

    def test_logout(self, user):

        url = reverse("account_logout")

        client = Client()
        client.force_login(user)

        # make sure I can't logout via a GET
        response = client.get(url)
        request_user = response.wsgi_request.user

        assert status.is_success(response.status_code)
        assert request_user == user and request_user.is_authenticated

        # make sure I _can_ logout w/ a token via a POST
        response = client.post(url)
        request_user = response.wsgi_request.user
        assert status.is_redirect(response.status_code)
        assert request_user != user and not request_user.is_authenticated
        assert response.url == get_adapter().get_logout_redirect_url(
            response.wsgi_request
        )
