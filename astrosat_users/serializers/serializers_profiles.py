from rest_framework import serializers


class GenericProfileListSerializer(serializers.ListSerializer):

    pass


def GenericProfileSerializerFactory(profile_class):
    class GenericProfileSerializer(serializers.ModelSerializer):
        class Meta:
            exclude = ("user", )
            list_serializer_class = GenericProfileListSerializer
            model = profile_class

    return GenericProfileSerializer
