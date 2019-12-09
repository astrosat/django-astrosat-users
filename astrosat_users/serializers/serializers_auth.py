from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from allauth.account.adapter import get_adapter
from allauth.account.forms import SetPasswordForm

from rest_auth.serializers import (
    LoginSerializer as RestAuthLoginSerializer,
    PasswordChangeSerializer as RestAuthPasswordChangeSerializer,
    PasswordResetSerializer as RestAuthPasswordResetSerializer,
    PasswordResetConfirmSerializer as RestAuthPasswordResetConfirmSerializer,
)
from rest_auth.registration.serializers import (
    RegisterSerializer as RestAuthRegisterSerializer,
)

from astrosat_users.conf import app_settings
from astrosat_users.forms import PasswordResetForm
from astrosat_users.models import User
from astrosat_users.utils import rest_decode_user_pk


class UserSerializerLite(serializers.ModelSerializer):
    """
    A lightweight read-only serializer used for passing the bare minimum amount
    of information about a user to the client; currently only used for login errors
    in-case the client needs that information to submit a POST (for example, to resend
    the verification email)
    """
    class Meta:
        model = User
        fields = ("email", "name")
        read_only_fields = ("email", "name")


class LoginSerializer(RestAuthLoginSerializer):

    # just a bit more security...
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    is_verified = serializers.BooleanField(read_only=True)
    is_approved = serializers.BooleanField(read_only=True)

    # (even though I don't need the 'username' field, the 'validate()' fn checks its value)
    # (so I haven't bothered removing it; the client can deal w/ this)

    def validate(self, attrs):
        """
        Does the usual login validation,
        but adds some explicit checks for `is_verified` and `is_approved`
        (this is the right place to put it; the KnoxLoginView has its own
        KnoxTokenSerializer for users _and_ tokens, but it uses this serializer
        for the user and so validation will be checked when processing the view.)
        """

        instance = super().validate(attrs)

        user = instance["user"]
        user_serializer = UserSerializerLite(user)

        if app_settings.ASTROSAT_USERS_REQUIRE_VERIFICATION and not user.is_verified:
            # do not automatically re-send the verification email
            # send_email_confirmation(request, user)
            msg = {
                "user": user_serializer.data,
                "detail": f"{user} is not verified",
            }
            raise ValidationError(msg)

        if app_settings.ASTROSAT_USERS_REQUIRE_APPROVAL and not user.is_approved:
            msg = {
                "user": user_serializer.data,
                "detail": f"{user} is not approved",
            }
            raise ValidationError(msg)

        return instance


class RegisterSerializer(RestAuthRegisterSerializer):

    # just a bit more security...
    password1 = serializers.CharField(write_only=True, style={"input_type": "password"})
    password2 = serializers.CharField(write_only=True, style={"input_type": "password"})

    # no need to overwrite serializers/forms to use zxcvbn;
    # both of those hook into the allauth adapter
    # which uses settings.AUTH_PASSWORD_VALIDATORS which includes zxcvbn


class SendEmailVerificationSerializer(serializers.Serializer):

    email = serializers.EmailField()


class PasswordChangeSerializer(RestAuthPasswordChangeSerializer):

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

    # RestAuthPasswordChangeSerializer uses AllAuthChangePasswordForm
    # which hooks into adapter.set_password


class PasswordResetSerializer(RestAuthPasswordResetSerializer):

    # RestAuthPasswordChangeSerializer uses Django's PasswordResetForm
    # but I want it to use AllAuth's PasswordResetForm (actually, I want
    # it to use my override of that for reasons explained in "forms_auth.py")

    # TODO: I SHOULD GET THIS FROM settings INSTEAD OF HARD-CODING IT
    password_reset_form_class = PasswordResetForm


class PasswordResetConfirmSerializer(RestAuthPasswordResetConfirmSerializer):

    new_password1 = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    new_password2 = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    # RestAuthPasswordChangeSerializer uses exceptionsDjango's SetPasswordForm
    # in the long-term, I probably want to use AllAuth's SetPassworForm

    # set_password_form_class = SetPasswordForm

    def validate(self, attrs):
        # I am rewriting the validate fn, though b/c I use a different
        # token generator than the hard-coded one in the parent class

        self._errors = {}
        try:
            uid = rest_decode_user_pk(attrs["uid"])
            self.user = User._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise ValidationError({"uid": ["Invalid value"]})

        self.custom_validation(attrs)
        self.set_password_form = self.set_password_form_class(
            user=self.user, data=attrs
        )
        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)
        # this is the different bit...
        token_generator = get_adapter().default_token_generator
        if not token_generator.check_token(self.user, attrs["token"]):
            raise ValidationError({"token": ["Invalid value"]})

        return attrs
