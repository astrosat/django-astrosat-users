from rest_framework import serializers

from astrosat_users.models import UserRole, UserPermission


class UserPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPermission
        fields = ("id", "name", "description")


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ("id", "name", "description", "permissions")

    permissions = UserPermissionSerializer(many=True, required=False)
