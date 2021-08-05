import copy
import pytest
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from astrosat_users.tests.factories import MessageAttachmentFactory, MessageFactory
from astrosat.tests.utils import *

from astrosat_users.models import Message
from astrosat_users.tests.utils import *

from .factories import *

UserModel = get_user_model()


@pytest.mark.django_db
class TestMessages:
    def test_message_created_on_registration(self, user_data):

        client = APIClient()

        test_data = {
            "email": user_data["email"],
            "password1": user_data["password"],
            "password2": user_data["password"],
        }

        assert Message.objects.count() == 0

        url = reverse("rest_register")
        response = client.post(url, test_data)
        assert status.is_success(response.status_code)

        assert Message.objects.count() == 1
        message = Message.objects.get(user__email=test_data["email"])

        assert re.match(
            r".*Please Confirm Your E-mail Address", message.title
        ) is not None
        assert re.match(settings.DEFAULT_FROM_EMAIL, message.sender) is not None
        assert test_data["email"] in message.content

        # test on verify email
        # test on licence invite/etc


@pytest.mark.django_db
class TestMessagesAPI:
    def test_list_messages(self, user):

        N_MESSAGES = 10

        token, key = create_auth_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        messages = [
            MessageFactory(user=user, attachments=1) for _ in range(N_MESSAGES)
        ]

        url = reverse("messages-list", kwargs={"user_id": user.uuid})
        response = client.get(url)
        assert status.is_success(response.status_code)

        assert len(response.json()) == N_MESSAGES

    def test_retrieve_message(self, user):

        token, key = create_auth_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        message = MessageFactory(user=user, attachments=1)

        url = reverse(
            "messages-detail", kwargs={
                "user_id": user.uuid, "pk": message.id
            }
        )
        response = client.get(url)
        assert status.is_success(response.status_code)

        message_data = response.json()
        assert message_data["title"] == message.title
        assert message_data["content"] == message.content
        assert message_data["sender"] == message.sender
        assert len(message_data["attachments"]) == 1

    def test_update_message(self, user):
        # tests you can update "read" and "archived" fields
        # but no other fields

        token, key = create_auth_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        message = MessageFactory(user=user, attachments=1)
        assert message.read == False
        assert message.archived == False

        url = reverse(
            "messages-detail", kwargs={
                "user_id": user.uuid, "pk": message.id
            }
        )
        response = client.get(url)
        assert status.is_success(response.status_code)
        old_message_data = response.json()

        test_message_data = {
            "read": True,
            "archived": True,
            "title": shuffle_string(old_message_data["title"]),
            "sender": shuffle_string(old_message_data["sender"]),
            "content": shuffle_string(old_message_data["content"]),
            "attachments": [{
                "file": "some/other/file.png"
            }]
        }

        response = client.put(url, data=test_message_data)
        assert status.is_success(response.status_code)
        new_message_data = response.json()

        assert new_message_data["read"] != old_message_data["read"]
        assert new_message_data["archived"] != old_message_data["archived"]
        assert new_message_data["title"] == old_message_data["title"]
        assert new_message_data["sender"] == old_message_data["sender"]
        assert new_message_data["content"] == old_message_data["content"]
        assert new_message_data["attachments"] == old_message_data["attachments"
                                                                  ]

        message.refresh_from_db()
        assert message.read == True
        assert message.archived == True
        assert message.title == old_message_data["title"]
        assert message.sender == old_message_data["sender"]
        assert message.content == old_message_data["content"]
