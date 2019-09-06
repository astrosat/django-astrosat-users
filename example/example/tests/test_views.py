import pytest
import factory

from django.contrib.auth import get_user_model
from django.urls import resolve, reverse

from rest_framework import status
from rest_framework.test import APIClient

from allauth.account.utils import get_adapter, user_pk_to_url_str, url_str_to_user_pk


from .factories import *
from .utils import *


UserModel = get_user_model()


@pytest.mark.django_db
class TestUserViewSet:

    def test_get_current_user(self, user):
        """
        Tests that using the reserved username "current"
        will return the current user.
        """

        client = APIClient()
        client.force_login(user)

        url = reverse("users-detail", kwargs={"username": "current"})

        response = client.get(url)
        content = response.json()
        assert status.is_success(response.status_code)
        assert content["username"]  == user.username
