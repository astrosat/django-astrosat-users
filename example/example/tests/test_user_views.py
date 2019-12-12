from django.urls import resolve, reverse

import pytest
import urllib

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

    def test_filter_approved_users(self, admin):

        token, key = create_auth_token(admin)

        users = [UserFactory() for _ in range(10)]

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url_params = urllib.parse.urlencode({"is_approved": "true"})
        url = f"{reverse('users-list')}?{url_params}"

        response = client.get(url)
        assert status.is_success(response.status_code)
        assert len(response.json()) == 0

        for user in users:
            user.is_approved = True
            user.save()

        response = client.get(url)
        assert status.is_success(response.status_code)
        assert len(response.json()) == len(users)

    def test_filter_verified_users(self, admin):

        token, key = create_auth_token(admin)

        users = [UserFactory() for _ in range(10)]

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url_params = urllib.parse.urlencode({"is_verified": "true"})
        url = f"{reverse('users-list')}?{url_params}"

        response = client.get(url)
        assert status.is_success(response.status_code)
        assert len(response.json()) == 1

        for user in users:
            user.verify()

        response = client.get(url)
        assert status.is_success(response.status_code)
        assert len(response.json()) == len(users) + 1

    def test_filter_roles_users(self, admin):

        token, key = create_auth_token(admin)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        users = [UserFactory() for _ in range(8)]
        roles = [UserRoleFactory() for _ in range(4)]

        # user 0 has no roles
        # user 1 has role 0
        # user 2 has role 1
        # user 3 has role 2
        # user 4 has role 3
        # user 5 has roles 0,1
        # user 6 has roles 1,2
        # user 7 has roles 2,3

        users[1].roles.add(roles[0])
        users[2].roles.add(roles[1])
        users[3].roles.add(roles[2])
        users[4].roles.add(roles[3])
        users[5].roles.add(roles[0], roles[1])
        users[6].roles.add(roles[1], roles[2])
        users[7].roles.add(roles[2], roles[3])

        url_params = urllib.parse.urlencode(
            {"roles__any": ",".join([role.name for role in roles[:2]])}
        )
        url = f"{reverse('users-list')}?{url_params}"

        response = client.get(url)
        actual_data = response.json()
        expected_data = [users[1].id, users[2].id, users[5].id, users[6].id]
        assert status.is_success(response.status_code)
        assert len(actual_data) == len(expected_data)
        assert set(map(lambda x: x["id"], actual_data)) == set(expected_data)

        url_params = urllib.parse.urlencode(
            {"roles__all": ",".join([role.name for role in roles[:2]])}
        )
        url = f"{reverse('users-list')}?{url_params}"

        response = client.get(url)
        actual_data = response.json()
        expected_data = [users[5].id]
        assert status.is_success(response.status_code)
        assert len(actual_data) == len(expected_data)
        assert set(map(lambda x: x["id"], actual_data)) == set(expected_data)

    def test_filter_permissions_users(self, admin):

        token, key = create_auth_token(admin)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        users = [UserFactory() for _ in range(8)]
        permissions = [UserPermissionFactory() for _ in range(4)]
        roles = [UserRoleFactory(permissions=[permissions[i]]) for i in range(4)]

        # user 0 has no permissions
        # user 1 has permission 0
        # user 2 has permission 1
        # user 3 has permission 2
        # user 4 has permission 3
        # user 5 has permissions 0,1
        # user 6 has permissions 1,2
        # user 7 has permissions 2,3

        users[1].roles.add(roles[0])
        users[2].roles.add(roles[1])
        users[3].roles.add(roles[2])
        users[4].roles.add(roles[3])
        users[5].roles.add(roles[0], roles[1])
        users[6].roles.add(roles[1], roles[2])
        users[7].roles.add(roles[2], roles[3])

        url_params = urllib.parse.urlencode(
            {
                "permissions__any": ",".join(
                    [permission.name for permission in permissions[:2]]
                )
            }
        )
        url = f"{reverse('users-list')}?{url_params}"

        response = client.get(url)
        actual_data = response.json()
        expected_data = [users[1].id, users[2].id, users[5].id, users[6].id]
        assert status.is_success(response.status_code)
        assert len(actual_data) == len(expected_data)
        assert set(map(lambda x: x["id"], actual_data)) == set(expected_data)

        url_params = urllib.parse.urlencode(
            {
                "permissions__all": ",".join(
                    [permission.name for permission in permissions[:2]]
                )
            }
        )
        url = f"{reverse('users-list')}?{url_params}"

        response = client.get(url)
        actual_data = response.json()
        expected_data = [users[5].id]
        assert status.is_success(response.status_code)
        assert len(actual_data) == len(expected_data)
        assert set(map(lambda x: x["id"], actual_data)) == set(expected_data)

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
