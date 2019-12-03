from rest_framework import serializers

from .serializers_auth import LoginSerializer


class KnoxTokenSerializer(serializers.Serializer):
    user = LoginSerializer()
    token = serializers.SerializerMethodField()

    def get_token(self, obj):
        instance, token = obj["token"]
        return token

    # TODO: DO _REAL_ VALIDATION ON THE TOKEN
