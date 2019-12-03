from django.urls import resolve, reverse

import pytest
import factory

from rest_framework import status
from rest_framework.test import APIClient

from rest_auth.models import TokenModel
from rest_auth.app_settings import TokenSerializer, create_token

from astrosat_users.models import User
from astrosat_users.tests.utils import *

from .factories import *


@pytest.mark.django_db
class TestApiViews:
    def test_list_users(self, admin):

        token, key = create_auth_token(admin)

        users = [UserFactory() for _ in range(10)]

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("users-list")
        response = client.get(url)
        data = response.json()

        assert status.is_success(response.status_code)
        assert len(data) == len(users) + 1  # (add 1 for the admin user)

        for actual_data, test_data in zip(data, [admin] + users):
            assert actual_data["id"] == test_data.id
            assert actual_data["email"] == test_data.email

    def test_get_user(self, admin):

        token, key = create_auth_token(admin)

        test_user = UserFactory()

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("users-detail", kwargs={"email": test_user.email})
        response = client.get(url)
        data = response.json()

        assert status.is_success(response.status_code)
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email

    def test_put_user(self, admin):
        """
        Tests that I can update the user.
        And the updates get persisted.
        """
        token, key = create_auth_token(admin)

        test_user = UserFactory(name="before")

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("users-detail", kwargs={"email": test_user.email})

        response = client.get(url)
        data = response.json()

        assert status.is_success(response.status_code)
        assert data["name"] == "before"

        data["name"] = "after"

        response = client.put(url, data, format="json")
        data = response.json()

        assert status.is_success(response.status_code)
        assert data["name"] == "after"

        test_user.refresh_from_db()
        assert test_user.name == "after"

    def test_get_current_user(self):
        """
        Tests that using the reserved username "current"
        will return the current user.
        """

        client = APIClient()
        for _ in range(4):
            user = UserFactory()
            token, key = create_auth_token(user)
            client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
            url = reverse("users-detail", kwargs={"email": "current"})
            response = client.get(url)
            content = response.json()
            assert status.is_success(response.status_code)
            # make sure that "current" returns the user whose key is passed
            assert content["email"] == user.email
