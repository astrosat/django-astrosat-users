import pytest
import urllib

from django.urls import resolve, reverse

from rest_framework import status
from rest_framework.test import APIClient

from dj_rest_auth.models import TokenModel
from dj_rest_auth.app_settings import TokenSerializer, create_token

from astrosat.tests.utils import *

from astrosat_users.models import User
from astrosat_users.tests.utils import *

from .factories import *


@pytest.mark.django_db
class TestApiViews:

    users_list_url = reverse("users-list")

    def test_list_users(self, admin, mock_storage):

        token, key = create_auth_token(admin)

        users = [UserFactory() for _ in range(10)]

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        response = client.get(self.users_list_url)
        content = response.json()

        assert status.is_success(response.status_code)
        assert len(content) == len(users) + 1  # (add 1 for the admin user)

        for response_data, db_data in zip(content, [admin] + users):
            assert response_data["email"] == db_data.email

    def test_filter_approved_users(self, admin, mock_storage):

        token, key = create_auth_token(admin)

        users = [UserFactory(is_approved=i % 2) for i in range(10)]

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        url_params = urllib.parse.urlencode({"is_approved": "true"})

        response = client.get(f"{self.users_list_url}?{url_params}")
        content = response.json()

        assert status.is_success(response.status_code)
        assert len(content) == 5

        for response_data, db_data in zip(content, users[1::2]):
            assert response_data["email"] == db_data.email
            assert response_data["is_approved"] == True

    def test_filter_accepted_terms_users(self, admin, mock_storage):

        token, key = create_auth_token(admin)

        users = [UserFactory(accepted_terms=i % 2) for i in range(10)]

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        url_params = urllib.parse.urlencode({"accepted_terms": "true"})

        response = client.get(f"{self.users_list_url}?{url_params}")
        content = response.json()

        assert status.is_success(response.status_code)
        assert len(content) == 5

        for response_data, db_data in zip(content, users[1::2]):
            assert response_data["email"] == db_data.email
            assert response_data["accepted_terms"] == True

    def test_filter_verified_users(self, admin, mock_storage):

        token, key = create_auth_token(admin)

        users = [UserFactory() for i in range(10)]
        for i, user in enumerate(users):
            if i % 2:
                user.verify()

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        url_params = urllib.parse.urlencode({"is_verified": "true"})

        response = client.get(f"{self.users_list_url}?{url_params}")
        content = response.json()

        assert status.is_success(response.status_code)
        assert len(content) == 5 + 1  # (don't forget the admin)

        for response_data, db_data in zip(content[1:], users[1::2]):
            assert response_data["email"] == db_data.email
            assert response_data["is_verified"] == True

    def test_filter_roles_users(self, admin, mock_storage):

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
        matching_users = [users[1], users[2], users[5], users[6]]

        response = client.get(f"{self.users_list_url}?{url_params}")
        content = response.json()

        assert status.is_success(response.status_code)
        assert len(content) == len(matching_users)
        assert set(map(lambda x: x["email"],
                       content)) == set(map(lambda x: x.email, matching_users))

        url_params = urllib.parse.urlencode(
            {"roles__all": ",".join([role.name for role in roles[:2]])}
        )
        matching_users = [users[5]]

        response = client.get(f"{self.users_list_url}?{url_params}")
        content = response.json()

        assert status.is_success(response.status_code)
        assert len(content) == len(matching_users)
        assert set(map(lambda x: x["email"],
                       content)) == set(map(lambda x: x.email, matching_users))

    def test_filter_permissions_users(self, admin, mock_storage):

        token, key = create_auth_token(admin)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        users = [UserFactory() for _ in range(8)]
        permissions = [UserPermissionFactory() for _ in range(4)]
        roles = [
            UserRoleFactory(permissions=[permissions[i]]) for i in range(4)
        ]

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
                "permissions__any":
                    ",".join(
                        [permission.name for permission in permissions[:2]]
                    )
            }
        )
        matching_users = [users[1], users[2], users[5], users[6]]

        response = client.get(f"{self.users_list_url}?{url_params}")
        content = response.json()

        assert status.is_success(response.status_code)
        assert len(content) == len(matching_users)
        assert set(map(lambda x: x["email"],
                       content)) == set(map(lambda x: x.email, matching_users))

        url_params = urllib.parse.urlencode(
            {
                "permissions__all":
                    ",".join(
                        [permission.name for permission in permissions[:2]]
                    )
            }
        )
        matching_users = [users[5]]

        response = client.get(f"{self.users_list_url}?{url_params}")
        content = response.json()

        assert status.is_success(response.status_code)
        assert len(content) == len(matching_users)
        assert set(map(lambda x: x["email"],
                       content)) == set(map(lambda x: x.email, matching_users))

    def test_get_user(self, admin, mock_storage):

        token, key = create_auth_token(admin)

        test_user = UserFactory()

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("users-detail", kwargs={"id": test_user.uuid})
        response = client.get(url)
        data = response.json()

        assert status.is_success(response.status_code)
        assert data["email"] == test_user.email

    def test_put_user(self, admin, mock_storage):
        """
        Tests that I can update the user.
        And the updates get persisted.
        """
        token, key = create_auth_token(admin)

        test_user = UserFactory(name="before", avatar=None)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        url = reverse("users-detail", kwargs={"id": test_user.uuid})

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

    def test_get_current_user(self, mock_storage):
        """
        Tests that using the reserved username "current"
        will return the current user.
        """

        client = APIClient()
        users = [UserFactory() for _ in range(4)]
        for user in users:
            token, key = create_auth_token(user)
            client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
            url = reverse("users-detail", kwargs={"id": "current"})
            response = client.get(url)
            content = response.json()
            assert status.is_success(response.status_code)
            # make sure that "current" returns the user whose key is passed
            assert content["email"] == user.email
