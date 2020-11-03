import pytest
import factory

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core import mail
from django.test import Client
from django.urls import resolve, reverse

from allauth.utils import build_absolute_uri

from rest_framework import status
from rest_framework.test import APIClient

from astrosat.tests.utils import *

from astrosat_users.conf import app_settings
from astrosat_users.tests.utils import *
from astrosat_users.views.views_auth import REGISTRATION_CLOSED_MSG

from .factories import *

UserModel = get_user_model()


@pytest.mark.django_db
class TestApiRegistration:

    registration_url = reverse("rest_register")
    verification_url = reverse("rest_verify_email")

    def test_disable_registration(self, user_settings):
        """
        Tests that you cannot register when registration is closed
        """

        client = APIClient()

        user_settings.allow_registration = True
        user_settings.save()

        # get is never allowed
        response = client.get(self.registration_url)
        assert status.is_client_error(response.status_code)

        user_settings.allow_registration = False
        user_settings.save()

        # get/post are not allowed if allow_registration is False
        response = client.get(self.registration_url)
        assert status.is_client_error(response.status_code)
        assert response.json()["detail"] == REGISTRATION_CLOSED_MSG
        response = client.post(self.registration_url)
        assert status.is_client_error(response.status_code)
        assert response.json()["detail"] == REGISTRATION_CLOSED_MSG

    def test_registration(self, user_data):
        """
        Tests that registering a user results in an un-verified un-approved user
        """

        client = APIClient()

        test_data = {
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
        }

        response = client.post(self.registration_url, test_data)
        assert status.is_success(response.status_code)

        assert UserModel.objects.count() == 1
        user = UserModel.objects.get(email=user_data["email"])
        assert user.is_active == True
        assert user.is_verified == False
        assert user.is_approved == False
        assert user.accepted_terms == False

    def test_registration_accept_terms(self, user_data, user_settings):

        client = APIClient()

        user_settings.require_terms_acceptance = True
        user_settings.save()

        test_data = {
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
        }

        response = client.post(self.registration_url, test_data)
        assert status.is_client_error(response.status_code)

        test_data.update({"accepted_terms": True})

        response = client.post(self.registration_url, test_data)
        assert status.is_success(response.status_code)

    def test_registration_sends_confirmation_email(self, user_data):
        """
        Tests that registering a user sends a single email
        """
        client = APIClient()

        test_data = {
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
        }

        assert len(mail.outbox) == 0
        response = client.post(self.registration_url, test_data)

        user = UserModel.objects.get(email=test_data["email"])

        confirmation_url = build_absolute_uri(
            response.wsgi_request,
            app_settings.ACCOUNT_CONFIRM_EMAIL_CLIENT_URL.format(
                key=user.latest_confirmation_key
            ),
        )
        assert len(mail.outbox) == 1
        email = mail.outbox[0]

        assert test_data["email"] in email.to
        assert confirmation_url in email.body

    def test_registration_sends_notification_email(
        self, user_settings, user_data
    ):
        """
        Tests that registering a user sends an email to the admin
        """

        if not user_settings.notify_signups:
            user_settings.notify_signups = True
            user_settings.save()

        client = APIClient()

        test_data = {
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
        }

        assert len(mail.outbox) == 0
        client.post(self.registration_url, test_data)

        user = UserModel.objects.get(email=test_data["email"])
        email = mail.outbox[0]

        manager_emails = [manager[1] for manager in settings.MANAGERS]

        assert manager_emails == email.to
        assert user.email in email.body

    def test_registration_verify_email(self, user_settings, user_data):

        client = APIClient()

        test_data = {
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
        }

        client.post(self.registration_url, test_data)

        user = UserModel.objects.get(email=test_data["email"])
        valid_user_key = user.latest_confirmation_key
        invalid_user_key = shuffle_string(valid_user_key)

        response = client.post(self.verification_url, {"key": invalid_user_key})
        assert status.is_client_error(response.status_code)
        assert user.is_verified is False

        response = client.post(self.verification_url, {"key": valid_user_key})
        assert status.is_success(response.status_code)
        assert user.is_verified is True

        content = response.json()
        assert user.username == content["user"]["username"]

    def test_resend_verify_email(self, user):

        assert user.is_verified is False

        valid_email = user.email
        invalid_email = shuffle_string(user.username
                                      ) + "@" + valid_email.split("@")[1]

        client = APIClient()
        url = reverse("rest_send_email_verification")

        # an invalid email raises an error...
        response = client.post(url, {"email": invalid_email})
        assert status.is_client_error(response.status_code)
        assert len(mail.outbox) == 0

        # a valid email sends a message...
        response = client.post(url, {"email": valid_email})
        assert status.is_success(response.status_code)
        assert len(mail.outbox) == 1

        # a verified user does nothing...
        user.verify()
        user.save()
        response = client.post(url, {"email": valid_email})
        assert status.is_success(response.status_code)
        assert len(mail.outbox) == 1


@pytest.mark.django_db
class TestBackendRegistration:

    registration_url = reverse("account_signup")

    def test_disable_backend(self, user_settings):
        """
        Tests that you cannot access backend views when it's disabled.
        """

        client = Client()

        user_settings.enable_backend_access = True
        user_settings.save()

        response = client.get(self.registration_url)
        assert status.is_success(response.status_code)

        user_settings.enable_backend_access = False
        user_settings.save()

        response = client.get(self.registration_url)
        assert status.is_redirect(response.status_code)
        assert resolve(response.url).view_name == "disabled"

    def test_disable_registration(self, user_settings):
        """
        Tests that you cannot register when registration is closed
        """

        client = Client()

        response = client.get(self.registration_url)
        assert status.is_success(response.status_code)
        assert any(
            map(
                lambda template: template.name == "account/signup.html",
                response.templates,
            )
        )

        user_settings.allow_registration = False
        user_settings.save()

        response = client.get(self.registration_url)
        assert status.is_success(response.status_code)
        assert any(
            map(
                lambda template: template.name == "account/signup_closed.html",
                response.templates,
            )
        )

    def test_registration(self, user_data, user_settings):
        """
        Tests that registering a user results in an un-verified un-approved user
        """

        client = Client()

        test_data = {
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
            "accepted_terms": True,
        }

        response = client.post(self.registration_url, test_data)

        assert status.is_redirect(response.status_code)
        assert resolve(
            response.url
        ).view_name == "account_email_verification_sent"

        user = UserModel.objects.get(email=user_data["email"])
        assert UserModel.objects.count() == 1
        assert user.is_active == True
        assert user.is_verified == False
        assert user.is_approved == False

    def test_registration_accept_terms(self, user_data, user_settings):

        client = Client()

        user_settings.require_terms_acceptance = True
        user_settings.save()

        test_data = {
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
        }

        response = client.post(self.registration_url, test_data)
        request_user = response.wsgi_request.user

        assert status.is_success(response.status_code)
        assert not request_user.is_authenticated

        test_data.update({"accepted_terms": True})

        response = client.post(self.registration_url, test_data)
        request_user = response.wsgi_request.user

        assert status.is_redirect(response.status_code)
        assert not request_user.is_authenticated
        assert resolve(
            response.url
        ).view_name == "account_email_verification_sent"

    def test_registration_sends_confirmation_email(self, user_data):
        """
        Tests that registering a user sends an email
        """

        client = Client()

        test_data = {
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
        }

        assert len(mail.outbox) == 0
        client.post(self.registration_url, test_data)

        user = UserModel.objects.get(email=test_data["email"])
        confirmation_url = reverse(
            "account_confirm_email",
            kwargs={"key": user.latest_confirmation_key}
        )
        email = mail.outbox[0]

        assert test_data["email"] in email.to
        assert confirmation_url in email.body

    def test_registration_sends_notification_email(
        self, user_settings, user_data
    ):
        """
        Tests that registering a user sends an email to the admin
        """

        if not user_settings.notify_signups:
            user_settings.notify_signups = True
            user_settings.save()

        client = Client()

        test_data = {
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
        }

        assert len(mail.outbox) == 0
        client.post(self.registration_url, test_data)

        user = UserModel.objects.get(email=test_data["email"])
        email = mail.outbox[0]

        manager_emails = [manager[1] for manager in settings.MANAGERS]

        assert manager_emails == email.to
        assert user.email in email.body

    def test_registration_verify_email(self, user_settings, user_data):

        client = Client()

        test_data = {
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
        }

        client.post(self.registration_url, test_data)

        user = UserModel.objects.get(email=test_data["email"])
        valid_verification_url = reverse(
            "account_confirm_email",
            kwargs={"key": user.latest_confirmation_key}
        )
        invalid_verification_url = reverse(
            "account_confirm_email",
            kwargs={"key": shuffle_string(user.latest_confirmation_key)},
        )

        response = client.post(invalid_verification_url)
        assert status.is_client_error(response.status_code)
        assert user.is_verified is False

        response = client.post(valid_verification_url)
        assert status.is_redirect(response.status_code)
        assert user.is_verified is True
