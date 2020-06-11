from rest_framework import serializers

from astrosat_users.models import User, UserRole, UserPermission, PROFILES_REGISTRY


class UserSerializerLite(serializers.ModelSerializer):
    """
    A lightweight read-only serializer used for passing the bare minimum amount
    of information about a user to the client; currently only used for login errors
    in-case the client needs that information to submit a POST (for example, to resend
    the verification email, and for the RegisterView)
    """

    class Meta:
        model = User
        fields = ("email", "name", "username", "change_password")
        read_only_fields = ("email", "name", "username", "change_password")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "change_password",
            "email",
            "name",
            "description",
            "is_active",
            "is_verified",
            "is_approved",
            "accepted_terms",
            "profiles",
            "roles",
            "permissions",
            "customers",
        )

    profiles = serializers.SerializerMethodField()
    roles = serializers.SlugRelatedField(many=True, queryset=UserRole.objects.all(), slug_field="name")
    permissions = serializers.SerializerMethodField()
    customers = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")

    def get_profiles(self, obj):
        profiles = {}
        # see comment in "views_users.py" about managed_profiles
        managed_profiles = self.context.get("managed_profiles", [])
        for profile_key, profile in obj.profiles.items():
            if profile and profile_key in managed_profiles:
                profile_serializer_class = profile.get_serializer_class()
                profiles[profile_key] = profile_serializer_class(profile).data
        return profiles

    def get_permissions(self, obj):
        """
        returns a read-only list of permissions belonging to the user
        """
        roles_qs = obj.roles.exclude(permissions__isnull=True)
        permission_names_qs = roles_qs.values_list("permissions__name", flat=True)
        return permission_names_qs.distinct()

    def to_representation(self, instance):

        profiles_representation = {}
        for profile_key, profile in instance.profiles.items():
            if profile:
                profile_serializer_class = profile.get_serializer_class()
                profiles_representation[
                    profile_key
                ] = profile_serializer_class().to_representation(profile)

        representation = super().to_representation(instance)
        representation.update({"profiles": profiles_representation})

        return representation

    def to_internal_value(self, data):
        """
        Puts back any non-model and/or non-writeable fields as needed,
        so that their data is available in validated_data for create/update below.
        """

        profiles_internal_value = {}

        if "profiles" in data:
            for profile_key, profile_data in data["profiles"].items():
                profile_class = PROFILES_REGISTRY[profile_key]
                profile_serializer_class = profile_class.get_serializer_class()
                profiles_internal_value[
                    profile_key
                ] = profile_serializer_class().to_internal_value(profile_data)

        internal_value = super().to_internal_value(data)

        internal_value.update({"profiles": profiles_internal_value})

        return internal_value

    def update(self, instance, validated_data):

        profiles_data = validated_data.pop("profiles")
        if profiles_data:
            for profile_key, profile_data in profiles_data.items():
                profile_class = PROFILES_REGISTRY[profile_key]
                profile_serializer_class = profile_class.get_serializer_class()
                profile_serializer_class().update(
                    getattr(instance, profile_key), profile_data
                )
        updated_instance = super().update(instance, validated_data)

        return updated_instance
