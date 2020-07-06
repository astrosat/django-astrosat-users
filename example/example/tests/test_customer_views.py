import pytest
import urllib

from django.urls import resolve, reverse

from rest_framework import status
from rest_framework.test import APIClient

from dj_rest_auth.models import TokenModel
from dj_rest_auth.app_settings import TokenSerializer, create_token

from astrosat.tests.utils import *

from astrosat_users.tests.factories import CustomerFactory
from astrosat_users.tests.utils import *

from .factories import *


@pytest.mark.django_db
class TestCustomerViews:
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

        new_name = shuffle_string(content["name"])
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

    # TODO: TEST POST CUSTOMER_USERS

    def test_get_customer_user(self, admin, mock_storage):

        N_CUSTOMER_USERS = 10

        customer = CustomerFactory(logo=None)
        customer_users = [
            customer.add_user(UserFactory(avatar=None), type="MEMBER", status="ACTIVE")[0]
            for _ in range(N_CUSTOMER_USERS)
        ]

        test_user = customer_users[0].user

        _, key = create_auth_token(admin)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("customer-users-detail", args=[customer.id, test_user.email])

        response = client.get(url, format="json")
        content = response.json()

        assert status.is_success(response.status_code)
        assert content["user"]["id"] == test_user.id

    def test_update_customer_user(self, admin, mock_storage):

        N_CUSTOMER_USERS = 10

        customer = CustomerFactory(logo=None)
        customer_users = [
            customer.add_user(UserFactory(avatar=None), type="MEMBER", status="ACTIVE")[0]
            for _ in range(N_CUSTOMER_USERS)
        ]

        test_user = customer_users[0].user

        _, key = create_auth_token(admin)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("customer-users-detail", args=[customer.id, test_user.email])

        response = client.get(url, format="json")
        content = response.json()

        new_name = shuffle_string(content["user"]["name"])
        content["user"]["name"] = new_name

        response = client.put(url, content, format="json")
        assert status.is_success(response.status_code)
        test_user.refresh_from_db()
        assert test_user.name == new_name

    def test_delete_customer_user(self, admin, mock_storage):

        N_CUSTOMER_USERS = 10

        customer = CustomerFactory(logo=None)
        customer_users = [
            customer.add_user(UserFactory(avatar=None), type="MEMBER", status="ACTIVE")[0]
            for _ in range(N_CUSTOMER_USERS)
        ]

        test_user = customer_users[0].user

        _, key = create_auth_token(admin)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("customer-users-detail", args=[customer.id, test_user.email])

        response = client.delete(url)
        assert status.is_success(response.status_code)
        test_user.refresh_from_db()

        # make sure the customer_user is deleted, but the user still exists
        assert customer.customer_users.count() == N_CUSTOMER_USERS - 1
        assert test_user.customer_users.count() == 0
