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
from astrosat_users.models.models_users import UserRegistrationStageType
from astrosat_users.serializers import UserSerializerBasic, CustomerUserSerializer
from astrosat_users.views.views_customers import IsManagerPermission

from .factories import *


@pytest.mark.django_db
class TestCustomerViews:
    def test_create_customer_permission(self, user, mock_storage):

        customer_data = factory.build(dict, FACTORY_CLASS=CustomerFactory)
        customer_data["type"] = customer_data.pop("customer_type")
        customer_data.pop("logo")

        _, key = create_auth_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("customers-list")

        # a user that is not in the middle of creating a customer
        # cannot create a customer
        user.registration_stage = None
        user.save()

        response = client.post(url, customer_data, format="json")
        content = response.json()
        user.refresh_from_db()

        assert status.is_client_error(response.status_code)
        assert content[
            "detail"
        ] == "User must have a registration_stage of 'CUSTOMER' to perform this action."

        assert Customer.objects.count() == 0
        assert user.registration_stage != UserRegistrationStageType.CUSTOMER_USER

        # a user that IS in the middle of creating a customer
        # CAN create a customer (and is primed to create a customer_user)
        user.registration_stage = str(UserRegistrationStageType.CUSTOMER)
        user.save()

        response = client.post(url, customer_data, format="json")
        content = response.json()
        user.refresh_from_db()

        assert status.is_success(response.status_code)

        assert Customer.objects.count() == 1
        assert user.registration_stage == UserRegistrationStageType.CUSTOMER_USER

    def test_get_customer(self, user, mock_storage):

        # make sure user is a MANAGER of customer
        # (so they have permission for the view)
        customer = CustomerFactory(logo=None)
        (customer_user,
         _) = customer.add_user(user, type="MANAGER", status="ACTIVE")

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
        (customer_user,
         _) = customer.add_user(user, type="MANAGER", status="ACTIVE")

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

        # in addition to making the change,
        # the view should also notify the user
        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert "Update on your customer" in message.subject

    def test_list_customer_users(self, mock_storage):

        N_CUSTOMER_USERS = 10

        customer = CustomerFactory(logo=None)
        for _ in range(N_CUSTOMER_USERS):
            customer_user, _ =customer.add_user(
                UserFactory(avatar=None), type="MEMBER", status="ACTIVE"
            )

        # the user making the request must be a manager
        customer_user.customer_user_type = "MANAGER"
        customer_user.save()

        _, key = create_auth_token(customer_user.user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("customer-users-list", args=[customer.id])

        response = client.get(url, format="json")
        content = response.json()

        assert status.is_success(response.status_code)
        assert len(content) == N_CUSTOMER_USERS

    def test_get_customer_user(self, mock_storage):

        N_CUSTOMER_USERS = 10

        customer = CustomerFactory(logo=None)
        customer_users = [
            customer.add_user(
                UserFactory(avatar=None), type="MEMBER", status="ACTIVE"
            )[0] for _ in range(N_CUSTOMER_USERS)
        ]

        # the user making the request must be a manager
        customer_users[0].customer_user_type = "MANAGER"
        customer_users[0].save()

        test_user = customer_users[0].user

        _, key = create_auth_token(test_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse(
            "customer-users-detail", args=[customer.id, test_user.uuid]
        )

        response = client.get(url, format="json")
        content = response.json()

        assert status.is_success(response.status_code)
        assert content["user"]["email"] == test_user.email

    def test_update_customer_user(self, mock_storage):

        N_CUSTOMER_USERS = 10

        customer = CustomerFactory(logo=None)
        customer_users = [
            customer.add_user(
                UserFactory(avatar=None), type="MEMBER", status="ACTIVE"
            )[0] for _ in range(N_CUSTOMER_USERS)
        ]

        # the user making the request must be a manager
        customer_users[0].customer_user_type = "MANAGER"
        customer_users[0].save()

        test_user = customer_users[0].user

        _, key = create_auth_token(test_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse(
            "customer-users-detail", args=[customer.id, test_user.uuid]
        )

        response = client.get(url, format="json")
        content = response.json()

        new_name = shuffle_string(content["user"]["name"]).strip()
        content["user"]["name"] = new_name

        response = client.put(url, content, format="json")
        assert status.is_success(response.status_code)
        test_user.refresh_from_db()
        assert test_user.name == new_name

        # in addition to making the change,
        # the view should also notify the user
        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert "Update on your account" in message.subject

    def test_delete_customer_user(self, mock_storage):

        N_CUSTOMER_USERS = 10

        customer = CustomerFactory(logo=None)
        customer_users = [
            customer.add_user(
                UserFactory(avatar=None), type="MEMBER", status="ACTIVE"
            )[0] for _ in range(N_CUSTOMER_USERS)
        ]

        # the user making the request must be a manager
        # and not the customer_user being deleted
        customer_users[1].customer_user_type = "MANAGER"
        customer_users[1].save()

        test_user = customer_users[0].user

        _, key = create_auth_token(customer_users[1].user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse(
            "customer-users-detail", args=[customer.id, test_user.uuid]
        )

        response = client.delete(url)
        assert status.is_success(response.status_code)
        test_user.refresh_from_db()

        # make sure the customer_user is deleted, but the user still exists
        assert customer.customer_users.count() == N_CUSTOMER_USERS - 1
        assert test_user.customer_users.count() == 0

    def test_customer_permissions(self, mock_storage):
        # tests that a customer MEMBER can access "safe" methods
        # but only a customer MANAGER can access "non-safe" methods

        customer = CustomerFactory(logo=None)

        customer_user_manager, _ = customer.add_user(UserFactory(avatar=None), type="MANAGER", status="ACTIVE")
        customer_user_member, _ = customer.add_user(UserFactory(avatar=None), type="MEMBER", status="ACTIVE")

        client = APIClient()
        _, manager_key = create_auth_token(customer_user_manager.user)
        _, member_key = create_auth_token(customer_user_member.user)

        url = reverse("customers-detail", args=[customer.id])

        # manager can GET...
        client.credentials(HTTP_AUTHORIZATION=f"Token {manager_key}")
        response = client.get(url)
        assert status.is_success(response.status_code)

        # member can GET...
        client.credentials(HTTP_AUTHORIZATION=f"Token {member_key}")
        response = client.get(url)
        assert status.is_success(response.status_code)

        data = {k: v for k, v in response.json().items() if v is not None}

        # manager can PUT...
        client.credentials(HTTP_AUTHORIZATION=f"Token {manager_key}")
        response = client.put(url, data)
        assert status.is_success(response.status_code)

        # member cannot PUT...
        client.credentials(HTTP_AUTHORIZATION=f"Token {member_key}")
        response = client.put(url, data)
        assert status.is_client_error(response.status_code)

    def test_customer_user_permissions(self, mock_storage):
        # tests that only a customer MANAGER can access methods
        # and a customer MEMBER cannot access methods

        customer = CustomerFactory(logo=None)

        customer_user_manager, _ = customer.add_user(UserFactory(avatar=None), type="MANAGER", status="ACTIVE")
        customer_user_member, _ = customer.add_user(UserFactory(avatar=None), type="MEMBER", status="ACTIVE")

        client = APIClient()
        _, manager_key = create_auth_token(customer_user_manager.user)
        _, member_key = create_auth_token(customer_user_member.user)

        url = reverse("customer-users-list", args=[customer.id])

        # manager can GET...
        client.credentials(HTTP_AUTHORIZATION=f"Token {manager_key}")
        response = client.get(url)
        assert status.is_success(response.status_code)

        # member cannot GET...
        client.credentials(HTTP_AUTHORIZATION=f"Token {member_key}")
        response = client.get(url)
        assert status.is_client_error(response.status_code)

    def test_add_existing_customer_user(self, mock_storage):

        customer = CustomerFactory(logo=None)

        # the user making the request must be a manager
        customer_user, _ = customer.add_user(UserFactory(avatar=None), type="MANAGER", status="ACTIVE")

        client = APIClient()
        _, key = create_auth_token(customer_user.user)
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        test_user = UserFactory(avatar=None)

        url = reverse("customer-users-list", args=[customer.id])

        data = {
            # no need to specify type/status - they have default values
            "customer": customer.name,
            "user": UserSerializerBasic(test_user).data,
        }
        response = client.post(url, data, format="json")
        assert status.is_success(response.status_code)

        customer.refresh_from_db()
        test_user.refresh_from_db()

        assert customer.customer_users.count() == 2
        assert test_user.customer_users.count() == 1
        assert customer.customer_users.filter(
            id__in=test_user.customer_users.all()
        ).exists()
        assert test_user.change_password is not True

    def test_add_new_customer_user_permissions(self, mock_storage):

        customer = CustomerFactory(logo=None)

        user = UserFactory()

        _, key = create_auth_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        url = reverse("customer-users-list", args=[customer.id])

        data = {
            "customer": customer.name,
            "user": UserSerializerBasic(user).data,
        }

        # a user who is neither admin nor manager cannot create a customer user
        # if registration_stage is not CUSTOMER_USER
        assert user.registration_stage != UserRegistrationStageType.CUSTOMER_USER
        response = client.post(url, data, format="json")

        assert status.is_client_error(response.status_code)
        # TODO: ERROR IN DRF CAUSING COMPOSED PERMISSIONS TO RETURN A GENERIC MESSAGE
        # assert content["detail"] == "User must have a registration_stage of 'CUSTOMER_USER' to perform this action."

        # a user who is neither admin nor manager can still create a customer user
        # if registration_stage is CUSTOMER_USER
        user.registration_stage = UserRegistrationStageType.CUSTOMER_USER
        user.save()
        response = client.post(url, data, format="json")
        user.refresh_from_db()

        assert status.is_success(response.status_code)
        assert user.registration_stage == None
        assert customer.users.count() == 1

    def test_add_new_customer_user(self, user_data, mock_storage):

        customer = CustomerFactory(logo=None)
        customer_user, _ = customer.add_user(UserFactory(avatar=None), type="MANAGER", status="ACTIVE")

        _, key = create_auth_token(customer_user.user)
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

        assert customer.customer_users.count() == 2
        assert customer.customer_users.filter(id__in=user.customer_users.all()
                                             ).exists()
        assert user.change_password is True
        assert user.accepted_terms is False
        assert user.email == content["user"]["email"]

    def test_add_new_invalid_customer_user(self, user_data, mock_storage):

        user_data["email"] = "invalid_email_address"

        customer = CustomerFactory(logo=None)
        customer_user, _ = customer.add_user(UserFactory(avatar=None), type="MANAGER", status="ACTIVE")

        _, key = create_auth_token(customer_user.user)
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

        assert customer.customer_users.count() != 2

    def test_cannot_add_duplicate_customer_user(self, user_data, mock_storage):
        customer = CustomerFactory(logo=None)
        customer_user, _ = customer.add_user(UserFactory(avatar=None), type="MANAGER", status="ACTIVE")

        _, key = create_auth_token(customer_user.user)
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
        assert content["non_field_errors"] == [
            "User is already a member of Customer."
        ]
        assert customer.customer_users.count() == 2

    def test_add_new_customer_user_sends_email(self, user_data, mock_storage):

        customer = CustomerFactory(logo=None)
        customer_user, _ = customer.add_user(UserFactory(avatar=None), type="MANAGER", status="ACTIVE")

        _, key = create_auth_token(customer_user.user)
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

        (customer_user_1,
         _) = customer.add_user(user_1, type="MANAGER", status="ACTIVE")
        (customer_user_2,
         _) = customer.add_user(user_2, type="MANAGER", status="ACTIVE")

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

    def test_delete_customer_user_sends_email(self, user, mock_storage):

        customer = CustomerFactory(logo=None)
        customer_user, _ = customer.add_user(UserFactory(avatar=None), type="MANAGER", status="ACTIVE")

        customer.add_user(user, type="MEMBER", status="ACTIVE")

        _, key = create_auth_token(customer_user.user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("customer-users-detail", args=[customer.id, user.uuid])

        assert len(mail.outbox) == 0

        response = client.delete(url)
        assert status.is_success(response.status_code)

        email = mail.outbox[0]
        assert len(mail.outbox) == 1
        assert user.email in email.to

    def test_resend_invitation_new_customer_user(self, user_data, mock_storage):

        customer = CustomerFactory(logo=None)
        customer_user, _ = customer.add_user(UserFactory(avatar=None), type="MANAGER", status="ACTIVE")

        _, key = create_auth_token(customer_user.user)
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

        url = reverse(
            "customer-users-invite",
            args=[customer.id, old_content["user"]["id"]]
        )
        response = client.post(url, {}, format="json")
        assert status.is_success(response.status_code)
        new_content = response.json()

        assert new_content["invitation_date"] != old_content["invitation_date"]
        assert new_content["invitation_date"] is not None
        assert new_content["user"]["change_password"] is True

        INVITATION_RESET_PASSWORD_TEXT = "Please follow the link below to create a User Account and Password"

        assert len(mail.outbox) == 2
        assert INVITATION_RESET_PASSWORD_TEXT in mail.outbox[0].body
        assert INVITATION_RESET_PASSWORD_TEXT in mail.outbox[1].body

    def test_resend_invitation_existing_customer_user(self, user, mock_storage):

        customer = CustomerFactory(logo=None)
        customer.add_user(user, type="MANAGER", status="ACTIVE")

        customer_user, _ = customer.add_user(UserFactory(avatar=None), type="MEMBER", status="PENDING")

        _, key = create_auth_token(user)
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

        INVITATION_RESET_PASSWORD_TEXT = "Please follow the link below to create a User Account and Password"
        INVITATION_LOGIN_TEXT = "Please follow the link below to login"

        assert len(mail.outbox) == 1
        assert INVITATION_RESET_PASSWORD_TEXT not in mail.outbox[0].body
        assert INVITATION_LOGIN_TEXT in mail.outbox[0].body

    def test_onboard_customer_user(self, user, mock_storage):

        customer = CustomerFactory(logo=None)

        customer.add_user(user, type="MANAGER", status="ACTIVE")

        _, key = create_auth_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("customer-users-onboard", args=[customer.id, user.uuid])

        assert user.onboarded is False

        response = client.post(url, {}, format="json")
        content = response.json()
        user.refresh_from_db()

        assert status.is_success(response.status_code)
        assert content["user"]["onboarded"] is True
        assert user.onboarded is True

        EXAMPLE_ONBOARDING_TEXT = "Welcome to the example project!"

        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert EXAMPLE_ONBOARDING_TEXT in message.body
        assert len(message.cc) == 0  # emails should not be cc'd

    def test_customer_user_assign_manager(self, user, mock_storage):

        customer = CustomerFactory(logo=None)
        customer.add_user(user, type="MANAGER", status="ACTIVE")

        customer_user, _ = customer.add_user(UserFactory(avatar=None), type="MEMBER", status="ACTIVE")

        customer_user_data = CustomerUserSerializer(customer_user).data

        _, key = create_auth_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse(
            "customer-users-detail",
            args=[customer.id, customer_user.user.uuid]
        )

        customer_user_data["type"] = "MANAGER"
        response = client.put(url, customer_user_data, format="json")
        assert status.is_success(response.status_code)
        customer_user.refresh_from_db()

        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert "Admin right granted" in message.subject

    def test_customer_user_revoke_manager(self, user, mock_storage):

        customer = CustomerFactory(logo=None)
        customer.add_user(user, type="MANAGER", status="ACTIVE")

        customer_user, _ = customer.add_user(user, type="MANAGER", status="ACTIVE")
        customer_user_data = CustomerUserSerializer(customer_user).data

        _, key = create_auth_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse(
            "customer-users-detail",
            args=[customer.id, customer_user.user.uuid]
        )

        customer_user_data["type"] = "MEMBER"
        response = client.put(url, customer_user_data, format="json")
        assert status.is_success(response.status_code)
        customer_user.refresh_from_db()

        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert "Admin right revoked" in message.subject
