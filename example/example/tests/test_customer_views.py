import pytest
import urllib

from django.core import mail
from django.urls import resolve, reverse

from rest_framework import status
from rest_framework.test import APIClient

from dj_rest_auth.models import TokenModel
from dj_rest_auth.app_settings import TokenSerializer, create_token

from astrosat.tests.utils import *

from astrosat_users.tests.factories import CustomerFactory
from astrosat_users.tests.utils import *

from astrosat_users.models import User, Customer
from astrosat_users.serializers import UserSerializerBasic
from astrosat_users.views.views_customers import RequiresCustomerRegistrationCompletion, IsAdminOrManager

from .factories import *


@pytest.mark.django_db
class TestCustomerViews:

    def test_create_customer_permission(self, user, mock_storage):
        """
        ensures that a user w/out requires_customer_registration_completion cannot create a customer
        """

        customer_data = factory.build(dict, FACTORY_CLASS=CustomerFactory)
        customer_data["type"] = customer_data.pop("customer_type")
        customer_data.pop("logo")

        _, key = create_auth_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("customers-list")

        assert user.requires_customer_registration_completion is False

        response = client.post(url, customer_data, format="json")
        content = response.json()

        assert status.is_client_error(response.status_code)
        assert Customer.objects.count() == 0
        assert content["detail"] == RequiresCustomerRegistrationCompletion.message

    def test_create_customer(self, user, mock_storage):
        """
        ensures that a user w/ requires_customer_registration_completion can create a customer
        """

        customer_data = factory.build(dict, FACTORY_CLASS=CustomerFactory)
        customer_data["type"] = customer_data.pop("customer_type")
        customer_data.pop("logo")

        _, key = create_auth_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("customers-list")

        user.requires_customer_registration_completion = True
        user.save()

        response = client.post(url, customer_data, format="json")
        content = response.json()

        assert status.is_success(response.status_code)
        assert Customer.objects.count() == 1
        assert str(Customer.objects.first().id) == content["id"]

    def test_get_customer(self, user, mock_storage):

        # make sure user is a MANAGER of customer
        # (so they have permission for the view)
        customer = CustomerFactory(logo=None)
        (customer_user, _) = customer.add_user(user, type="MANAGER", status="ACTIVE")

        _, key = create_auth_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("customers-detail", args=[customer.id])

        response = client.get(url, format="json")
        content = response.json()

        assert status.is_success(response.status_code)

    def test_update_customer(self, user, mock_storage):

        # make sure user is a MANAGER of customer
        # (so they have permission for the view)
        customer = CustomerFactory(logo=None)
        (customer_user, _) = customer.add_user(user, type="MANAGER", status="ACTIVE")

        _, key = create_auth_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("customers-detail", args=[customer.id])

        response = client.get(url, format="json")
        content = response.json()

        new_name = shuffle_string(content["name"]).strip()
        content["name"] = new_name

        response = client.put(url, content, format="json")
        assert status.is_success(response.status_code)

        customer.refresh_from_db()
        assert customer.name == new_name

    def test_list_customer_users(self, admin, mock_storage):

        N_CUSTOMER_USERS = 10

        customer = CustomerFactory(logo=None)
        for _ in range(N_CUSTOMER_USERS):
            customer.add_user(UserFactory(avatar=None), type="MEMBER", status="ACTIVE")

        _, key = create_auth_token(admin)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("customer-users-list", args=[customer.id])

        response = client.get(url, format="json")
        content = response.json()

        assert status.is_success(response.status_code)
        assert len(content) == N_CUSTOMER_USERS

    def test_get_customer_user(self, admin, mock_storage):

        N_CUSTOMER_USERS = 10

        customer = CustomerFactory(logo=None)
        customer_users = [
            customer.add_user(UserFactory(avatar=None), type="MEMBER", status="ACTIVE")[
                0
            ]
            for _ in range(N_CUSTOMER_USERS)
        ]

        test_user = customer_users[0].user

        _, key = create_auth_token(admin)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("customer-users-detail", args=[customer.id, test_user.uuid])

        response = client.get(url, format="json")
        content = response.json()

        assert status.is_success(response.status_code)
        assert content["user"]["email"] == test_user.email

    def test_update_customer_user(self, admin, mock_storage):

        N_CUSTOMER_USERS = 10

        customer = CustomerFactory(logo=None)
        customer_users = [
            customer.add_user(UserFactory(avatar=None), type="MEMBER", status="ACTIVE")[
                0
            ]
            for _ in range(N_CUSTOMER_USERS)
        ]

        test_user = customer_users[0].user

        _, key = create_auth_token(admin)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("customer-users-detail", args=[customer.id, test_user.uuid])

        response = client.get(url, format="json")
        content = response.json()

        new_name = shuffle_string(content["user"]["name"]).strip()
        content["user"]["name"] = new_name

        response = client.put(url, content, format="json")
        assert status.is_success(response.status_code)
        test_user.refresh_from_db()
        assert test_user.name == new_name

    def test_delete_customer_user(self, admin, mock_storage):

        N_CUSTOMER_USERS = 10

        customer = CustomerFactory(logo=None)
        customer_users = [
            customer.add_user(UserFactory(avatar=None), type="MEMBER", status="ACTIVE")[
                0
            ]
            for _ in range(N_CUSTOMER_USERS)
        ]

        test_user = customer_users[0].user

        _, key = create_auth_token(admin)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("customer-users-detail", args=[customer.id, test_user.uuid])

        response = client.delete(url)
        assert status.is_success(response.status_code)
        test_user.refresh_from_db()

        # make sure the customer_user is deleted, but the user still exists
        assert customer.customer_users.count() == N_CUSTOMER_USERS - 1
        assert test_user.customer_users.count() == 0

    def test_member_cannot_access_customers(self, user, mock_storage):
        # tests that a customer MEMBER (not MANAGER) cannot access the Customers nor CustomerUsers API

        customer = CustomerFactory(logo=None)
        (customer_user, _) = customer.add_user(user, type="MEMBER", status="ACTIVE")

        _, key = create_auth_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        customer_url = reverse("customers-detail", args=[customer.id])
        customer_users_url = reverse("customer-users-list", args=[customer.id])

        response = client.get(customer_url, format="json")
        content = response.json()
        assert status.is_client_error(response.status_code)
        assert content["detail"] == IsAdminOrManager.message

        response = client.get(customer_users_url, format="json")
        content = response.json()
        assert status.is_client_error(response.status_code)
        assert content["detail"] == IsAdminOrManager.message

    def test_add_existing_customer_user(self, admin, mock_storage):

        customer = CustomerFactory(logo=None)

        user = UserFactory(avatar=None)

        _, key = create_auth_token(admin)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        url = reverse("customer-users-list", args=[customer.id])

        data = {
            # no need to specify type/status - they have default values
            "customer": customer.name,
            "user": UserSerializerBasic(user).data,
        }
        response = client.post(url, data, format="json")
        content = response.json()

        assert status.is_success(response.status_code)

        customer.refresh_from_db()
        user.refresh_from_db()

        assert customer.customer_users.count() == user.customer_users.count() == 1
        assert set(customer.customer_users.values_list("id")) == set(user.customer_users.values_list("id"))
        assert user.change_password is not True

    def test_add_new_customer_user(self, admin, user_data, mock_storage):

        customer = CustomerFactory(logo=None)

        _, key = create_auth_token(admin)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        url = reverse("customer-users-list", args=[customer.id])

        data = {
            # no need to specify type/status - they have default values
            "customer": customer.name,
            "user": user_data,
        }
        response = client.post(url, data, format="json")
        content = response.json()

        assert status.is_success(response.status_code)

        customer.refresh_from_db()
        user = User.objects.get(email=user_data["email"])

        assert customer.customer_users.count() == 1
        assert user.change_password is True
        assert user.pk in customer.customer_users.values_list("user", flat=True)
        assert user.email == content["user"]["email"]

    def test_add_new_invalid_customer_user(self, admin, user_data, mock_storage):

        user_data["email"] = "invalid_email_address"

        customer = CustomerFactory(logo=None)

        _, key = create_auth_token(admin)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        url = reverse("customer-users-list", args=[customer.id])

        data = {
            # no need to specify type/status - they have default values
            "customer": customer.name,
            "user": user_data,
        }
        response = client.post(url, data, format="json")
        content = response.json()

        customer.refresh_from_db()

        assert status.is_client_error(response.status_code)
        assert content["user"] == {"email": ["Enter a valid email address."]}

        assert customer.customer_users.count() == 0

    def test_cannot_add_duplicate_customer_user(self, admin, user_data, mock_storage):
        customer = CustomerFactory(logo=None)

        _, key = create_auth_token(admin)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        url = reverse("customer-users-list", args=[customer.id])

        data = {
            # no need to specify type/status - they have default values
            "customer": customer.name,
            "user": user_data,
        }
        response = client.post(url, data, format="json")  # this should succeed
        response = client.post(url, data, format="json")  # but this should fail
        content = response.json()

        assert status.is_client_error(response.status_code)
        assert content["non_field_errors"] == ["User is already a member of Customer."]
        assert customer.customer_users.count() == 1

    def test_add_new_customer_user_sends_email(self, admin, user_data, mock_storage):

        customer = CustomerFactory(logo=None)

        _, key = create_auth_token(admin)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        url = reverse("customer-users-list", args=[customer.id])
        assert len(mail.outbox) == 0

        data = {
            # no need to specify type/status - they have default values
            "customer": customer.name,
            "user": user_data,
        }
        response = client.post(url, data, format="json")

        adapter = get_adapter_from_response(response)
        password_reset_url = adapter.get_password_confirmation_url(
            response.wsgi_request,
            User.objects.get(email=user_data["email"]),
        )

        email = mail.outbox[0]
        assert len(mail.outbox) == 1
        assert user_data["email"] in email.to
        assert password_reset_url in email.body

    def test_customer_user_cannot_delete_self(self, mock_storage):

        customer = CustomerFactory(logo=None)
        user_1 = UserFactory(avatar=None)
        user_2 = UserFactory(avatar=None)

        (customer_user_1, _) = customer.add_user(user_1, type="MANAGER", status="ACTIVE")
        (customer_user_2, _) = customer.add_user(user_2, type="MANAGER", status="ACTIVE")

        _, key = create_auth_token(user_1)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        # user_1 cannot delete customer_user_1
        url = reverse("customer-users-detail", args=[customer.id, user_1.uuid])
        response = client.delete(url)
        assert status.is_client_error(response.status_code)
        assert customer.customer_users.count() == 2

        # user_1 can delete customer_user_2
        url = reverse("customer-users-detail", args=[customer.id, user_2.uuid])
        response = client.delete(url)
        assert status.is_success(response.status_code)
        assert customer.customer_users.count() == 1

    def test_delete_customer_user_sends_email(self, admin, user, mock_storage):

        customer = CustomerFactory(logo=None)

        (customer_user, _) = customer.add_user(user, type="MEMBER", status="ACTIVE")

        _, key = create_auth_token(admin)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("customer-users-detail", args=[customer.id, user.uuid])

        assert len(mail.outbox) == 0
        response = client.delete(url)

        email = mail.outbox[0]
        assert len(mail.outbox) == 1
        assert user.email in email.to

    def test_resend_invitation_new_customer_user(self, admin, user_data, mock_storage):

        customer = CustomerFactory(logo=None)

        _, key = create_auth_token(admin)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        url = reverse("customer-users-list", args=[customer.id])
        data = {
            "customer": customer.name,
            "user": user_data,
        }
        response = client.post(url, data, format="json")
        assert status.is_success(response.status_code)
        old_content = response.json()

        assert old_content["invitation_date"] is not None
        assert old_content["user"]["change_password"] is True

        url = reverse("customer-users-invite", args=[customer.id, old_content["user"]["id"]])
        response = client.post(url, {}, format="json")
        assert status.is_success(response.status_code)
        new_content = response.json()

        assert new_content["invitation_date"] != old_content["invitation_date"]
        assert new_content["invitation_date"] is not None
        assert new_content["user"]["change_password"] is True

        RESET_PASSWORD_TEXT = "Please follow the link below to create a User Account and Password"

        assert len(mail.outbox) == 2
        assert RESET_PASSWORD_TEXT in mail.outbox[0].body
        assert RESET_PASSWORD_TEXT in mail.outbox[1].body

    def test_resend_invitation_existing_customer_user(self, admin, user, mock_storage):

        customer = CustomerFactory(logo=None)

        (customer_user, _) = customer.add_user(user, type="MEMBER", status="PENDING")

        _, key = create_auth_token(admin)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("customer-users-invite", args=[customer.id, user.uuid])

        assert customer_user.invitation_date is None
        assert customer_user.user.change_password is False

        response = client.post(url, {}, format="json")
        content = response.json()

        assert status.is_success(response.status_code)
        assert content["invitation_date"] is not None
        assert content["user"]["change_password"] is False

        RESET_PASSWORD_TEXT = "Please follow the link below to create a User Account and Password"

        assert len(mail.outbox) == 1
        assert RESET_PASSWORD_TEXT not in mail.outbox[0].body
