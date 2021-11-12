from rest_framework import serializers

from example.models import ExampleProfile


class ExampleProfileSerializer(serializers.ModelSerializer):
    """
    A silly serializer, just for testing.
    """
    class Meta:
        model = ExampleProfile
        fields = (
            "age",
            "height",
            "weight",
            "body_mass_index",
            "some_custom_readonly_field",
        )

    some_custom_readonly_field = serializers.SerializerMethodField()

    def get_some_custom_readonly_field(self, obj):
        return "I am proof that this is a custom rather than a generic serializer"
