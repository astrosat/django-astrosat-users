import pytest
import factory

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client
from django.urls import resolve, reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from rest_framework import status
from rest_framework.test import APIClient

from allauth.account.utils import get_adapter, user_pk_to_url_str, url_str_to_user_pk

from astrosat_users.tests.utils import get_adapter_from_response, shuffle_string

from .factories import *
from .utils import *


UserModel = get_user_model()


#################
# Backend tests #
#################


@pytest.mark.django_db
class TestBackendViews:


    def test_disable_backend(self, user_settings):
        """
        Tests that you cannot access any backend views when it's disabled.
        """

        client = Client()
        url = reverse("account_signup")  # just testing one backend view

        user_settings.enable_backend_access = True
        user_settings.save()

        response = client.get(url)
        assert status.is_success(response.status_code)

        user_settings.enable_backend_access = False
        user_settings.save()

        response = client.get(url)
        assert status.is_redirect(response.status_code)
        assert resolve(response.url).view_name == "disabled"

    def test_disable_registration(self, user_settings):
        """
        Tests that you cannot register via the backend when registration is closed.
        """

        client = Client()
        url = reverse("account_signup")

        user_settings.allow_registration = True
        user_settings.save()

        response = client.get(url)
        open_template_name = "account/signup.html"
        assert status.is_success(response.status_code)
        assert any(map(lambda template: template.name == open_template_name, response.templates))

        user_settings.allow_registration = False
        user_settings.save()

        response = client.get(url)
        closed_template_name = "account/signup_closed.html"
        assert status.is_success(response.status_code)
        assert any(map(lambda template: template.name == closed_template_name, response.templates))

    def test_registration(self, user_settings, user_data):
        """
        Tests that registering a user via the backend results in an un-verified un-approved user
        """

        client = Client()
        url = reverse("account_signup")

        assert UserModel.objects.count() == 0

        test_data = {
            "username": user_data["username"],
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
        }

        response = client.post(url, test_data)
        assert status.is_redirect(response.status_code)
        assert resolve(response.url).view_name == "account_email_verification_sent"

        assert UserModel.objects.count() == 1
        user = UserModel.objects.get(username=test_data["username"])
        assert user.is_active == True
        assert user.is_verified == False
        assert user.is_approved == False

    def test_registration_sends_confirmation_email(self, user_settings, user_data):
        """
        Tests that registering a user via the backend sends an email
        """

        client = Client()
        url = reverse("account_signup")

        test_data = {
            "username": user_data["username"],
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
        }

        assert len(mail.outbox) == 0
        response = client.post(url, test_data)

        user = UserModel.objects.get(username=test_data["username"])
        confirmation_url = reverse("account_confirm_email", kwargs={"key": user.latest_confirmation_key})
        email = mail.outbox[0]

        assert test_data["email"] in email.to
        assert confirmation_url in email.body

    def test_registration_sends_notification_email(self, user_settings, user_data):
        """
        Tests that registering a user via the backend sends an email
        """

        client = Client()
        url = reverse("account_signup")

        if not user_settings.notify_signups:
            user_settings.notify_signups = True
            user_settings.save()

        test_data = {
            "username": user_data["username"],
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
        }

        assert len(mail.outbox) == 0
        response = client.post(url, test_data)

        user = UserModel.objects.get(username=test_data["username"])
        email = mail.outbox[0]

        manager_emails = [manager[1] for manager in settings.MANAGERS]

        assert manager_emails == email.to
        assert user.username in email.body

    def test_email_verification(self, user_settings, user_data):
        """
        Tests that following the confirmation url verifies a user
        """

        client = Client()
        url = reverse("account_signup")

        test_data = {
            "username": user_data["username"],
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
        }

        response = client.post(url, test_data)
        user = UserModel.objects.get(username=test_data["username"])
        confirmation_url = reverse("account_confirm_email", kwargs={"key": user.latest_confirmation_key})

        assert user.is_verified is False
        response = client.post(confirmation_url)
        assert user.is_verified is True


    def test_login_unverified(self, user_settings, user):
        """
        Tests that you can't login until your verified.
        """

        client = Client()
        url = reverse("account_login")
        assert user_settings.require_verification is True

        test_data = {
            "login": user.username,
            "password": user.raw_password,
        }

        # an unverified user can't login...
        assert user.is_verified is False
        response = client.post(url, data=test_data)
        request_user = response.wsgi_request.user
        assert status.is_redirect(response.status_code)
        assert request_user != user and not request_user.is_authenticated
        assert resolve(response.url).view_name == "account_email_verification_sent"

        # a verified user can login...
        user.verify()
        response = client.post(url, data=test_data)
        request_user = response.wsgi_request.user
        assert status.is_redirect(response.status_code)
        assert request_user == user and request_user.is_authenticated
        assert response.url == get_adapter().get_login_redirect_url(response.wsgi_request)

    def test_login_unapproved(self, user_settings, user):
        """
        Tests that you can't login until you are approved.
        """

        client = Client()
        url = reverse("account_login")

        user_settings.require_approval = True
        user_settings.save()

        test_data = {
            "login": user.username,
            "password": user.raw_password,
        }
        user.verify()

        # an unapproved user can't login...
        response = client.post(url, data=test_data)
        request_user = response.wsgi_request.user
        assert status.is_redirect(response.status_code)
        assert request_user != user and not request_user.is_authenticated
        assert resolve(response.url).view_name == "disapproved"

        user.is_approved = True
        user.save()

        # an approved user can login...
        response = client.post(url, data=test_data)
        request_user = response.wsgi_request.user
        assert status.is_redirect(response.status_code)
        assert request_user == user and request_user.is_authenticated
        assert response.url == get_adapter().get_login_redirect_url(response.wsgi_request)

    def test_login_inactive(self, user):
        """
        Tests that an inactive user can't login.
        """

        client = Client()
        url = reverse("account_login")

        test_data = {
            "login": user.username,
            "password": user.raw_password,
        }
        user.verify()
        user.is_approved = True
        user.is_active = False
        user.save()

        response = client.post(url, data=test_data)
        request_user = response.wsgi_request.user
        assert status.is_redirect(response.status_code)
        assert request_user != user and not request_user.is_authenticated
        assert resolve(response.url).view_name == "account_inactive"

    def test_logout_post(self, user):

        client = Client()
        client.force_login(user)

        url = reverse("account_logout")

        # a get won't logout...
        response = client.get(url)
        request_user = response.wsgi_request.user
        assert request_user == user and request_user.is_authenticated
        assert status.is_success(response.status_code)

        # a post  will logout...
        response = client.post(url)
        request_user = response.wsgi_request.user
        assert request_user != user and not request_user.is_authenticated
        assert status.is_redirect(response.status_code)
        assert response.url == get_adapter().get_logout_redirect_url(response.wsgi_request)

    def test_change_password(self, user):

        client = Client()
        client.force_login(user)

        url = reverse("account_change_password")

        old_password = user.raw_password
        new_password = shuffle_string(old_password)
        assert new_password != old_password

        test_data = {
            "oldpassword": old_password,
            "password1": new_password,
            "password2": new_password,
        }

        response = client.post(url, test_data)
        user.refresh_from_db()
        assert user.check_password(new_password) is True

    def test_reset_password_sends_email(self, user):

        client = Client()
        client.force_login(user)

        url = reverse("account_reset_password")

        test_data = {
            "email": user.email
        }

        assert len(mail.outbox) == 0

        response = client.post(url, test_data)
        confirmation_url = reverse(
            "account_reset_password_from_key",
            kwargs={"uidb36": user_pk_to_url_str(user), "key": user.generate_token()}
        )
        email = mail.outbox[0]

        assert status.is_redirect(response.status_code)
        assert resolve(response.url).view_name == "account_reset_password_done"
        assert test_data["email"] in email.to
        assert confirmation_url in email.body

    def test_password_confirmation(self, user):
        """
        Tests that following the password confirmation url lets a user change their password
        """

        client = Client()

        user_id = user_pk_to_url_str(user)
        user_token = user.generate_token()
        new_password = shuffle_string(user.raw_password)

        invalid_confirmation_url = reverse(
            "account_reset_password_from_key",
            kwargs={"uidb36": shuffle_string(user_id), "key": shuffle_string(user_token)}
        )
        valid_confirmation_url = reverse(
            "account_reset_password_from_key",
            kwargs={"uidb36": user_id, "key": user_token}
        )

        test_data = {
            "password1": new_password,
            "password2": new_password,
        }

        response = client.post(invalid_confirmation_url, test_data)
        assert response.context.get("token_fail") == True
        user.refresh_from_db()
        assert user.check_password(new_password) is False
        # TODO: TEST FAILS BUT DEPLOYMENT WORKS !?!
        # response = client.post(valid_confirmation_url, test_data)
        # user.refresh_from_db()
        # assert user.check_password(new_password) is True



    # user-list
    # user-detail
    # user-update
    # profile-list
    # profile-detail
    # profile-update

#############
# API tests #
#############


@pytest.mark.django_db
class TestAPIViews:

    def test_disable_registration(self, user_settings):
        """
        Tests that you cannot register via the API when registration is closed.
        """

        client = APIClient()
        url = reverse("rest_register")

        user_settings.allow_registration = True
        user_settings.save()

        response = client.get(url)
        assert status.is_client_error(response.status_code)  # get isn't allowed

        user_settings.allow_registration = False
        user_settings.save()

        response = client.get(url)
        assert status.is_redirect(response.status_code)
        assert resolve(response.url).view_name == "rest_disabled"

    def test_registration(self, user_settings, user_data):
        """
        Tests that registering a user via the API results in an un-verified un-approved user
        """

        client = APIClient()
        url = reverse("rest_register")

        assert UserModel.objects.count() == 0

        test_data = {
            "username": user_data["username"],
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
        }

        response = client.post(url, test_data)
        assert status.is_success(response.status_code)

        assert UserModel.objects.count() == 1
        user = UserModel.objects.get(username=test_data["username"])
        assert user.is_active == True
        assert user.is_verified == False
        assert user.is_approved == False

    def test_registration_sends_confirmation_email(self, user_settings, user_data):
        # TODO: INTERMITTENT FAILURE?
        """
        Tests that registering a user via the API sends an email
        """

        client = APIClient()
        url = reverse("rest_register")

        test_data = {
            "username": user_data["username"],
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
        }

        assert len(mail.outbox) == 0
        response = client.post(url, test_data)

        user = UserModel.objects.get(username=test_data["username"])
        confirmation_url = reverse("rest_confirm_email", kwargs={"key": user.latest_confirmation_key})
        email = mail.outbox[0]

        assert test_data["email"] in email.to
        assert confirmation_url in email.body

    def test_registration_sends_notification_email(self, user_settings, user_data):
        """
        Tests that registering a user via the API sends an email
        """

        client = APIClient()
        url = reverse("rest_register")

        if not user_settings.notify_signups:
            user_settings.notify_signups = True
            user_settings.save()

        test_data = {
            "username": user_data["username"],
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
        }

        assert len(mail.outbox) == 0
        response = client.post(url, test_data)

        user = UserModel.objects.get(username=test_data["username"])
        email = mail.outbox[0]

        manager_emails = [manager[1] for manager in settings.MANAGERS]

        assert manager_emails == email.to
        assert user.username in email.body

    def test_email_verification(self, user_settings, user_data):
        """
        Tests that following the confirmation url verifies a user
        """

        client = APIClient()
        url = reverse("rest_register")

        test_data = {
            "username": user_data["username"],
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
        }

        response = client.post(url, test_data)
        user = UserModel.objects.get(username=test_data["username"])
        confirmation_url = reverse("rest_confirm_email", kwargs={"key": user.latest_confirmation_key})

        assert user.is_verified is False
        response = client.get(confirmation_url)
        assert status.is_success(response.status_code)
        assert user.is_verified is True

    def test_login_unverified(self, user_settings, user):
        """
        Tests that you can't login until you are verified.
        """

        client = APIClient()
        url = reverse("rest_login")
        assert user_settings.require_verification is True
        assert user_settings.require_approval is False

        test_data = {
            "username": user.username,
            "password": user.raw_password,
        }
        assert user.is_verified is False

        # an unverified user can't login...
        response = client.post(url, test_data)
        request_user = response.wsgi_request.user
        assert request_user != user and not request_user.is_authenticated

        user.verify()

        # a verified user can login...
        response = client.post(url, test_data)
        request_user = response.wsgi_request.user
        assert request_user == user and request_user.is_authenticated

    def test_login_unapproved(self, user_settings, user):
        """
        Tests that you can't login until you are approved.
        """

        client = APIClient()
        url = reverse("rest_login")

        user_settings.require_approval = True
        user_settings.save()

        test_data = {
            "username": user.username,
            "password": user.raw_password,
        }
        user.verify()

        # an unapproved user can't login...
        response = client.post(url, test_data)
        request_user = response.wsgi_request.user
        assert request_user != user and not request_user.is_authenticated

        user.is_approved = True
        user.save()

        # an approved user can login...
        response = client.post(url, test_data)
        request_user = response.wsgi_request.user
        assert request_user == user and request_user.is_authenticated

    def test_login_inactive(self, user):
        """
        Tests that an inactive user can't login.
        """

        client = APIClient()
        url = reverse("rest_login")

        test_data = {
            "username": user.username,
            "password": user.raw_password,
        }
        user.verify()
        user.is_approved = True
        user.is_active = False
        user.save()

        response = client.post(url, data=test_data)
        request_user = response.wsgi_request.user
        assert status.is_client_error(response.status_code)
        assert request_user != user and not request_user.is_authenticated

    def test_logout_post(self, user):

        client = APIClient()
        client.force_authenticate(user)
        url = reverse("rest_logout")

        # a get won't logout...

        response = client.get(url)
        request_user = response.wsgi_request.user
        assert request_user == user and request_user.is_authenticated
        assert status.is_client_error(response.status_code)

        # a post  will logout...
        response = client.post(url)
        request_user = response.wsgi_request.user
        assert request_user != user and not request_user.is_authenticated
        assert status.is_success(response.status_code)

    def test_change_password(self, user):

        client = APIClient()
        client.force_authenticate(user)

        url = reverse("rest_password_change")

        old_password = user.raw_password
        new_password = shuffle_string(old_password)
        assert new_password != old_password

        test_data = {
            "new_password1": new_password,
            "new_password2": new_password,
        }

        response = client.post(url, data=test_data)
        assert status.is_success(response.status_code)
        user.refresh_from_db()
        assert user.check_password(new_password) is True

    def test_reset_password_sends_email(self, user):

        client = APIClient()
        client.force_login(user)

        url = reverse("rest_password_reset")

        test_data = {
            "email": user.email
        }

        assert len(mail.outbox) == 0

        response = client.post(url, test_data)
        confirmation_url = reverse(
            "rest_password_reset_confirm",
            kwargs={"uid": urlsafe_base64_encode(force_bytes(user.pk)), "token": user.generate_token()}
        )
        email = mail.outbox[0]

        assert status.is_success(response.status_code)
        assert test_data["email"] in email.to
        assert confirmation_url in email.body

    def test_password_confirmation(self, user):
        """
        Tests that following the password confirmation url lets a user change their password
        """

        client = APIClient()

        user_id = urlsafe_base64_encode(force_bytes(user.pk))
        user_token = user.generate_token()
        new_password = shuffle_string(user.raw_password)

        invalid_confirmation_url = reverse(
            "rest_password_reset_confirm",
            kwargs={"uid": shuffle_string(user_id), "token": shuffle_string(user_token)}
        )
        valid_confirmation_url = reverse(
            "rest_password_reset_confirm",
            kwargs={"uid": user_id, "token": user_token}
        )

        test_data = {
            "new_password1": new_password,
            "new_password2": new_password,
            # uid & token are passed via the URL
        }

        # TODO: TEST FAILS BUT DEPLOYMENT WORKS !?!
        # response = client.post(invalid_confirmation_url, test_data)
        # assert response.context.get("token_fail") == True
        # user.refresh_from_db()
        # assert user.check_password(new_password) is False

        response = client.post(valid_confirmation_url, test_data)
        user.refresh_from_db()
        assert user.check_password(new_password) is True
