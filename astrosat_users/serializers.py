import inspect

from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode

from rest_framework import serializers

from rest_auth.serializers import (
    PasswordChangeSerializer as RestAuthPasswordChangeSerializer,
    PasswordResetSerializer as RestAuthPasswordResetSerializer,
    PasswordResetConfirmSerializer as RestAuthPasswordResetConfirmSerializer,
)
from rest_auth.registration.serializers import (
    RegisterSerializer as RestAuthRegisterSerializer,
)

from astrosat.serializers import WritableNestedListSerializer

from .forms import PasswordResetForm
from .models import User, UserRole, UserPermission
from .profiles import PROFILES, get_profile_qs
from .tokens import default_token_generator


###############################
# generic profile serializers #
###############################

class GenericProfileListSerializer(serializers.ListSerializer):

    pass


class GenericProfileSerializer(serializers.ModelSerializer):

    class Meta:
        list_serializer_class = GenericProfileListSerializer
        model = None
        exclude = ("user",)

    @classmethod
    def wrap_profile(cls, profile_key):
        cls.Meta.model = PROFILES[profile_key]
        return cls

#####################################
# roles and permissions serializers #
#####################################

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
            instances=instance.permissions.all(),
            validated_data=permissions_data,
        )

        if instance:
            instance = super().update(instance, validated_data)
        else:
            instance = super().create(validated_data)

        instance.permissions.clear()
        instance.permissions.add(*permissions)

        return instance

####################
# user serializers #
####################

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ("id", "username", "email", "name", "description", "is_verified", "is_approved", "profiles", "roles",)

    profiles = serializers.SerializerMethodField()
    roles = UserRoleSerializer(many=True, required=False)

    def get_profiles(self, obj):
        profiles = {}
        managed_profiles = self.context.get("managed_profiles", [])
        for profile_key, profile in obj.profiles.items():
            if profile_key in managed_profiles:
                profile_serializer = GenericProfileSerializer().wrap_profile(profile_key)
                profiles[profile_key] = profile_serializer(profile).data
        return profiles


    def to_internal_value(self, data):
        """
        Puts back any non-model and non-writeable fields as needed,
        so that their data is available in validated_data for create/update below.
        """

        profiles_internal_value = {}
        for profile_key, profile_data in data["profiles"].items():
            profile_serializer = GenericProfileSerializer().wrap_profile(profile_key)
            profiles_internal_value[profile_key] = profile_serializer().to_internal_value(profile_data)

        role_serializer = self.fields["roles"]
        roles_internal_value = data.pop(role_serializer.source)

        internal_value = super().to_internal_value(data)

        internal_value.update({
            "profiles": profiles_internal_value,
            "roles": roles_internal_value,
        })

        return internal_value



    def update(self, instance, validated_data):

        profiles_data = validated_data.pop("profiles")
        if profiles_data:
            for profile_key, profile_data in profiles_data.items():
                profile_serializer = GenericProfileSerializer().wrap_profile(profile_key)
                profile_instance = getattr(instance, profile_key)
                profile_serializer().update(profile_instance, profile_data)

        roles_serializer = self.fields["roles"]
        roles_data = validated_data.pop(roles_serializer.source)
        roles = roles_serializer.crud(
            instances=instance.roles.all(),
            validated_data=roles_data,
        )

        updated_instance = super().update(instance, validated_data)

        updated_instance.roles.clear()
        updated_instance.roles.add(*roles)

        return updated_instance


##############################
# authentication serializers #
##############################


class RegisterSerializer(RestAuthRegisterSerializer):

    # just a bit more security...
    password1 = serializers.CharField(write_only=True, style={"input_type": "password"})
    password2 = serializers.CharField(write_only=True, style={"input_type": "password"})


class PasswordChangeSerializer(RestAuthPasswordChangeSerializer):

    # just a bit more security...
    new_password1 = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password2 = serializers.CharField(write_only=True, style={"input_type": "password"})


class PasswordResetSerializer(RestAuthPasswordResetSerializer):

    # just making sure that rest_auth uses my custom form for validation
    # that form works the same as allauth, except it customizes the email message
    password_reset_form_class = PasswordResetForm


class PasswordResetConfirmSerializer(RestAuthPasswordResetConfirmSerializer):

    # just a bit more security...
    new_password1 = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password2 = serializers.CharField(write_only=True, style={"input_type": "password"})

    # TODO: I WOULD PREFER TO SET DEFAULT VALUES LIKE THIS RATHER THAN IN __init__ BELOW
    # uid = serializers.CharField(default=SimpleLazyObject(lambda serializer_field: serializer_field.context.get("view").kwargs.get("uid")))

    def __init__(self, *args, **kwargs):
        """
        Injects extra data (default & initial data) to serializer fields.
        Ordinarily, you are meant to override the APIView.set_context() to do this, but I don't want to mess w/ rest_auth too much
        So I can already access the data I care about from the default view's kwargs which are already available in the context b/c Django is cool
        """
        super().__init__(*args, **kwargs)
        view = self.context.get("view", None)
        if view:
            uid = view.kwargs.get("uid", None)
            token = view.kwargs.get("token", None)
            self.fields["uid"] = serializers.CharField(default=uid, initial=uid)
            self.fields["token"] = serializers.CharField(default=token, initial=token)

    def validate(self, attrs):
        """
        Just like the parent class, except I use the same token generator as allauth
        """
        self._errors = {}

        try:
            uid = force_text(urlsafe_base64_decode(attrs['uid']))
            self.user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise ValidationError({'uid': ['Invalid value']})

        self.custom_validation(attrs)

        self.set_password_form = self.set_password_form_class(
            user=self.user, data=attrs
        )
        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)
        if not default_token_generator.check_token(self.user, attrs['token']):
            raise ValidationError({'token': ['Invalid value']})

        return attrs
