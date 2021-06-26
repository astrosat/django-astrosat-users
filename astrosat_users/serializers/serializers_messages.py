from django.contrib.auth import get_user_model

from rest_framework import serializers

from astrosat.serializers import ContextVariableDefault
from astrosat_users.models import Message, MessageAttachment


class MessageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttachment
        fields = ("file", )


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = (
            "id",
            "read",
            "archived",
            "date",
            "title",
            "sender",
            "content",
            "attachments",
            "user",
        )
        read_only_fields = (
            "id",
            "date",
            "title",
            "sender",
            "content",
            "attachments",
        )

    user = serializers.PrimaryKeyRelatedField(
        default=ContextVariableDefault("user", raise_error=True),
        queryset=get_user_model().objects.all(),
        write_only=True,
    )

    attachments = MessageAttachmentSerializer(many=True, read_only=True)
