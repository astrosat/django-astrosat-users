from rest_framework import serializers

from example.models import ExampleProfile


class ExampleProfileSerializer(serializers.ModelSerializer):
    """
    A silly serializer, just for testing.
    """
    class Meta:
        model = ExampleProfile
        fields = ("age", "height", "weight", "body_mass_index",)
