import pytest

from django.urls import resolve, reverse

from rest_framework import status
from rest_framework.test import APIClient

from astrosat.tests.utils import *

from astrosat_users.tests.utils import *

from .factories import *


@pytest.mark.django_db
class TestUserViews:
    def test_get_user_profile(self, mock_storage):
        """
        Tests that a user's profile is serialized w/ that user
        """

        test_user = UserFactory(avatar=None)
        test_profile, test_profile_field = ["example_profile", "age"]

        url = reverse("users-detail", kwargs={"id": test_user.uuid})

        _, key = create_auth_token(test_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        response = client.get(url)
        assert status.is_success(response.status_code)

        content = response.json()

        assert test_profile in content["profiles"]

    def test_put_user_profile(self, mock_storage):
        """
        Tests that a user's profile can be updated via the Users API
        """

        test_user = UserFactory(avatar=None)
        test_profile, test_profile_field = ["example_profile", "age"]

        url = reverse("users-detail", kwargs={"id": test_user.uuid})

        _, key = create_auth_token(test_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        response = client.get(url)
        assert status.is_success(response.status_code)

        content = response.json()
        old_profile_field_content = content["profiles"][test_profile][
            test_profile_field]
        new_profile_field_content = old_profile_field_content + 100

        content["profiles"][test_profile][test_profile_field
                                         ] = new_profile_field_content

        response = client.put(url, content, format="json")
        assert status.is_success(response.status_code)

        new_content = response.json()
        assert new_content["profiles"][test_profile][
            test_profile_field] == new_profile_field_content

        test_user.refresh_from_db()
        assert getattr(
            getattr(test_user, test_profile), test_profile_field
        ) == new_profile_field_content


@pytest.mark.django_db
class TestProfileViews:
    def test_get_profile(self, mock_storage):

        test_user = UserFactory(avatar=None)
        test_profile, test_profile_field = ["example_profile", "age"]

        url = reverse(
            "user-profiles",
            kwargs={
                "user_id": test_user.uuid, "profile_name": test_profile
            }
        )

        _, key = create_auth_token(test_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        response = client.get(url)
        assert status.is_success(response.status_code)

        content = response.json()

        assert content[test_profile_field] == getattr(
            getattr(test_user, test_profile), test_profile_field
        )

    def test_put_profile(self, mock_storage):
        test_user = UserFactory(avatar=None)
        test_profile, test_profile_field = ["example_profile", "age"]

        url = reverse(
            "user-profiles",
            kwargs={
                "user_id": test_user.uuid, "profile_name": test_profile
            }
        )

        _, key = create_auth_token(test_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        response = client.get(url)
        assert status.is_success(response.status_code)

        content = response.json()
        old_profile_field_content = content[test_profile_field]
        new_profile_field_content = old_profile_field_content + 100

        content[test_profile_field] = new_profile_field_content

        response = client.put(url, content, format="json")
        assert status.is_success(response.status_code)

        new_content = response.json()
        assert new_content[test_profile_field] == new_profile_field_content

        test_user.refresh_from_db()
        assert getattr(
            getattr(test_user, test_profile), test_profile_field
        ) == new_profile_field_content
