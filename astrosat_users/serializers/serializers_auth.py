from django.utils.module_loading import import_string

from allauth.account import app_settings as auth_settings
from allauth.account.adapter import get_adapter
from allauth.account.views import ConfirmEmailView as AllAuthVerifyEmailView

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.settings import api_settings as drf_settings

from dj_rest_auth.serializers import (
    LoginSerializer as RestAuthLoginSerializer,
    PasswordChangeSerializer as RestAuthPasswordChangeSerializer,
    PasswordResetSerializer as RestAuthPasswordResetSerializer,
    PasswordResetConfirmSerializer as RestAuthPasswordResetConfirmSerializer,
)
from dj_rest_auth.registration.serializers import (
    RegisterSerializer as RestAuthRegisterSerializer,
)

from astrosat.serializers import ConsolidatedErrorsSerializerMixin

from astrosat_users.conf import app_settings
from astrosat_users.models import User
from astrosat_users.utils import rest_decode_user_pk

from .serializers_users import (
    UserSerializerLite,
)  # explicit import to prevent circular dependencies


class LoginSerializer(ConsolidatedErrorsSerializerMixin, RestAuthLoginSerializer):

    # just a bit more security...
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    # some extra fields...
    id = serializers.UUIDField(read_only=True, source="uuid")
    is_verified = serializers.BooleanField(read_only=True)
    is_approved = serializers.BooleanField(read_only=True)
    accepted_terms = serializers.BooleanField(read_only=True)
    change_password = serializers.BooleanField(read_only=True)

    # (even though I don't need the 'username' field, the 'validate()' fn checks its value)
    # (so I haven't bothered removing it; the client can deal w/ this)

    def validate(self, attrs):
        """
        Does the usual login validation, but as w/ LoginForm it adds some explicit checks for astrosat_users-specific stuff
        (this is the right place to put it; the KnoxLoginView has its own KnoxTokenSerializer for users _and_ tokens,
        but it uses this serializer for the user and so validation will be checked when processing the view.)
        """

        instance = super().validate(attrs)

        user = instance["user"]
        user_serializer = UserSerializerLite(user)

        adapter = get_adapter(self.context.get("request"))
        try:
            adapter.check_user(user)
        except Exception as e:
            msg = {
                "user": user_serializer.data,
                drf_settings.NON_FIELD_ERRORS_KEY: str(e),
            }
            raise ValidationError(msg)

        return instance


class PasswordChangeSerializer(
    ConsolidatedErrorsSerializerMixin, RestAuthPasswordChangeSerializer
):

    # just a bit more security...
    old_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    new_password1 = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    new_password2 = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    # TODO: dj-rest-auth USE Django SetPasswordForm INSTEAD OF Allauth SetPasswordForm; WHY ?!?
    # set_password_form_class = import_string(auth_settings.FORMS["set_password"])


class PasswordResetSerializer(
    ConsolidatedErrorsSerializerMixin, RestAuthPasswordResetSerializer
):

    password_reset_form_class = import_string(auth_settings.FORMS["reset_password"])

    def validate_email(self, value):
        # TODO: THERE IS AN ERROR IN django-rest-auth [https://github.com/Tivix/django-rest-auth/blob/624ad01afbc86fa15b4e652406f3bdcd01f36e00/rest_auth/serializers.py#L172]
        # TODO: WHICH WILL RETURN A NESTED ERROR UNLESS I OVERRIDE THIS FN
        self.reset_form = self.password_reset_form_class(data=self.initial_data)
        if not self.reset_form.is_valid():
            raise serializers.ValidationError(self.reset_form.errors["email"])
        return value


class PasswordResetConfirmSerializer(
    ConsolidatedErrorsSerializerMixin, RestAuthPasswordResetConfirmSerializer
):

    new_password1 = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    new_password2 = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    # TODO: dj-rest-auth USE Django SetPasswordForm INSTEAD OF Allauth SetPasswordForm; WHY ?!?
    # set_password_form_class = import_string(auth_settings.FORMS["set_password"])

    def validate(self, attrs):
        # I am rewriting the validate fn, b/c I use a different
        # token generator than the hard-coded one in the parent class

        self._errors = {}

        try:
            uid = rest_decode_user_pk(attrs["uid"])
            self.user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise ValidationError({"uid": ["Invalid value"]})

        # this is the different bit...
        token_generator = get_adapter().default_token_generator
        if not token_generator.check_token(self.user, attrs["token"]):
            raise ValidationError({"token": ["Invalid value"]})

        self.custom_validation(attrs)
        self.set_password_form = self.set_password_form_class(
            user=self.user, data=attrs
        )
        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)

        return attrs

    def save(self):
        # TODO: ONCE I FIGURE OUT HOW TO USE THE ALLAUTH FORM, I CAN REMOVE THIS
        user = self.set_password_form.save()
        if user.change_password:
            user.change_password = False
            user.save()
        return user


class RegisterSerializer(ConsolidatedErrorsSerializerMixin, RestAuthRegisterSerializer):

    # just a bit more security...
    password1 = serializers.CharField(write_only=True, style={"input_type": "password"})
    password2 = serializers.CharField(write_only=True, style={"input_type": "password"})

    # no need to overwrite serializers/forms to use zxcvbn;
    # both of those hook into the allauth adapter
    # which uses settings.AUTH_PASSWORD_VALIDATORS which includes zxcvbn

    # add extra fields...
    accepted_terms = serializers.BooleanField()

    def validate_accepted_terms(self, value):
        if app_settings.ASTROSAT_USERS_REQUIRE_TERMS_ACCEPTANCE and not value:
            raise serializers.ValidationError(
                "Accepting terms & conditions is required."
            )
        return value

    def get_cleaned_data(self):
        # this serializer pretends to be a form by passing "validated_data"
        # as "cleaned_data" to the adapter.save_user method; but the parent
        # class hard-codes the attributes - this is stupid (I didn't write it)
        # So I override this fn to simply return all serializer fields
        # (the adapter will ignore what it doesn't care about)
        return self.validated_data


class VerifyEmailSerializer(ConsolidatedErrorsSerializerMixin, serializers.Serializer):

    key = serializers.CharField()

    def validate(self, data):

        try:
            view = AllAuthVerifyEmailView()
            view.kwargs = (
                data
            )  # little hack here b/c I'm using a view outside a request
            emailconfirmation = view.get_object()
            data["confirmation"] = emailconfirmation
        except Exception:
            raise serializers.ValidationError("This is an invalid key.")

        return data


class SendEmailVerificationSerializer(
    ConsolidatedErrorsSerializerMixin, serializers.Serializer
):

    email = serializers.EmailField()

    def validate(self, data):

        email_data = data["email"]
        try:
            user = User.objects.get(email=email_data)
            data["user"] = user
        except User.DoesNotExist:
            raise serializers.ValidationError(
                f"Unable to find user with '{email_data}' address."
            )

        return data
