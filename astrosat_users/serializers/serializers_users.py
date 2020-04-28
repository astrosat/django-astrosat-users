from rest_framework import serializers

from astrosat.serializers import WritableNestedListSerializer

from astrosat_users.models import User, UserRole, UserPermission, PROFILES


class UserSerializerLite(serializers.ModelSerializer):
    """
    A lightweight read-only serializer used for passing the bare minimum amount
    of information about a user to the client; currently only used for login errors
    in-case the client needs that information to submit a POST (for example, to resend
    the verification email, and for the RegisterView)
    """

    class Meta:
        model = User
        fields = ("email", "name", "username")
        read_only_fields = ("email", "name", "username")


class GenericProfileListSerializer(serializers.ListSerializer):

    pass


class GenericProfileSerializer(serializers.ModelSerializer):
    class Meta:
        list_serializer_class = GenericProfileListSerializer
        model = None
        exclude = ("user",)

    @classmethod
    def wrap_profile(cls, profile):
        # wraps this _generic_ profile serializer around a _specific_ profile model
        cls.Meta.model = profile
        return cls


class UserPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPermission
        fields = ("id", "name", "description")
        list_serializer_class = WritableNestedListSerializer


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ("id", "name", "description", "permissions")
        list_serializer_class = WritableNestedListSerializer

    permissions = UserPermissionSerializer(many=True, required=False)

    def create(self, validated_data):
        return self.crud(instance=None, validated_data=validated_data)

    def update(self, instance, validated_data):
        return self.crud(instance=instance, validated_data=validated_data)

    def crud(self, instance=None, validated_data={}, delete_missing=False):

        permissions_serializer = self.fields["permissions"]
        permissions_data = validated_data.pop(permissions_serializer.source)
        permissions = permissions_serializer.crud(
            instances=instance.permissions.all(), validated_data=permissions_data
        )

        if instance:
            instance = super().update(instance, validated_data)
        else:
            instance = super().create(validated_data)

        instance.permissions.clear()
        instance.permissions.add(*permissions)

        return instance


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
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
        )

    profiles = serializers.SerializerMethodField()
    roles = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    permissions = serializers.SerializerMethodField()

    def get_permissions(self, obj):
        distinct_permission_names = obj.roles.values_list(
            "permissions__name", flat=True
        ).distinct()
        return distinct_permission_names

    def get_profiles(self, obj):
        profiles = {}
        # see comment in "views_api_users.py" about managed_profiles
        managed_profiles = self.context.get("managed_profiles", [])
        for profile_key, profile in obj.profiles.items():
            if profile_key in managed_profiles:
                profile_serializer = profile.get_serializer_class()
                profiles[profile_key] = profile_serializer(profile).data
        return profiles

    def to_representation(self, instance):

        profiles_representation = {}
        for profile_key, profile in instance.profiles.items():
            profile_serializer = profile.get_serializer_class()
            profiles_representation[
                profile_key
            ] = profile_serializer().to_representation(profile)

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
                profile_class = PROFILES[profile_key]
                profile_serializer = profile_class.get_serializer_class()
                profiles_internal_value[
                    profile_key
                ] = profile_serializer().to_internal_value(profile_data)


        internal_value = super().to_internal_value(data)

        internal_value.update({"profiles": profiles_internal_value})

        return internal_value

    def update(self, instance, validated_data):

        profiles_data = validated_data.pop("profiles")
        if profiles_data:
            for profile_key, profile_data in profiles_data.items():
                profile_class = PROFILES[profile_key]
                profile_serializer = profile_class.get_serializer_class()
                profile_serializer().update(
                    getattr(instance, profile_key), profile_data,
                )

                # profile_serializer = GenericProfileSerializer().wrap_profile(
                #     profile_key
                # )
                # profile_instance = getattr(instance, profile_key)
                # profile_serializer().update(profile_instance, profile_data)

        updated_instance = super().update(instance, validated_data)

        return updated_instance
