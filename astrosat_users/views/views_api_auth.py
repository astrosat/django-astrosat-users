from collections import OrderedDict

from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.utils.translation import ugettext_lazy as _

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import get_adapter
from allauth.account.utils import complete_signup, send_email_confirmation

from rest_auth.views import (
    LoginView as RestAuthLoginView,
    LogoutView as RestAuthLogoutView,
    PasswordChangeView as RestAuthPasswordChangeView,
    PasswordResetView as RestAuthPasswordResetView,
    PasswordResetConfirmView as RestAuthPasswordResetConfirmView,
)
from rest_auth.registration.views import (
    RegisterView as RestAuthRegisterView,
    VerifyEmailView as RestAuthVerifyEmailView,
)

from astrosat.decorators import conditional_redirect
from astrosat_users.conf import app_settings as astrosat_users_settings
from astrosat_users.models import User
from astrosat_users.serializers import (
    KnoxTokenSerializer,
    SendEmailVerificationSerializer,
)
from astrosat_users.utils import create_knox_token


class IsNotAuthenticated(BasePermission):
    def has_object_permission(self, request, view, obj):
        # anybody can do GET, HEAD, or OPTIONS
        if request.method in SAFE_METHODS:
            return True

        # only an unauthenticated user can do POST, PUT, PATCH, DELETE
        user = request.user
        return not user.is_authenticated


 # b/c ACCOUNT_USERNAME_REQURED is False and ACCOUNT_EMAIL_REQUIRED is True,
 # not all fields from the LoginSerializer are used in the LoginView
 # therefore, I overide the swagger documentation w/ the following schema
_login_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties=OrderedDict((
        # ("username", openapi.Schema(type=openapi.TYPE_STRING, example="admin")),
        ("email", openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, example="allyn.treshansky@astrosat.net")),
        ("password", openapi.Schema(type=openapi.TYPE_STRING, example="password")),
    ))
)


@method_decorator(
    swagger_auto_schema(
        request_body=_login_schema, responses={status.HTTP_200_OK: KnoxTokenSerializer}
    ),
    name="post",
)
@method_decorator(sensitive_post_parameters("password"), name="dispatch")
class LoginView(RestAuthLoginView):
    """
    Just like rest_auth.LoginView but removes all of the JWT logic
    """

    permission_classes = [IsNotAuthenticated]

    def get_response(self):
        # note that this uses the KnoxTokenSerializer
        # which has custom token validation
        # which includes the LoginSerializer
        # which adds extra astrosat_users validation
        serializer_class = self.get_response_serializer()

        data = {"user": self.user, "token": self.token}
        serializer = serializer_class(instance=data, context={"request": self.request})

        return Response(serializer.data, status=200)


class LogoutView(RestAuthLogoutView):
    """
    Just like rest_auth.LogoutView but deletes knox token
    prior to passing to logout
    """

    permission_classes = [IsAuthenticated]

    def logout(self, request):
        token = request.auth
        if token:
            token.delete()
        return super().logout(request)


@method_decorator(sensitive_post_parameters("password1", "password2"), name="dispatch")
@method_decorator(
    conditional_redirect(
        lambda: not astrosat_users_settings.ASTROSAT_USERS_ALLOW_REGISTRATION,
        redirect_name="rest_disabled",
    ),
    name="dispatch",
)
class RegisterView(RestAuthRegisterView):

    permission_classes = [IsNotAuthenticated]

    def get_response_data(self, user):
        return KnoxTokenSerializer({"user": user, "token": self.token}).data

    def perform_create(self, serializer):
        user = serializer.save(self.request)
        self.token = create_knox_token(None, user, None)
        complete_signup(
            self.request._request, user, allauth_settings.EMAIL_VERIFICATION, None
        )
        return user


class SendEmailVerificationView(GenericAPIView):
    """
    An endpoint which re-sends the confirmation email to the
    provided email address (no longer doing it automatically
    upon a failed login)
    """

    serializer_class = SendEmailVerificationSerializer

    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email_data = serializer.data["email"]

        try:
            user = User.objects.get(email=email_data)
        except User.DoesNotExist:
            raise ValidationError(f"Unable to find user with '{email_data}' address.")

        if not user.is_verified:
            send_email_confirmation(request, user)
            msg = _("Verification email sent.")
        else:
            msg = _(f"No verification email sent; {user} is already verified.")

        return Response({"detail": msg})


class VerifyEmailView(RestAuthVerifyEmailView):
    """
    This is the endpoint that the client POSTS to after having recieved
    the "account_confirm_email" view.
    takes the following parameters:
    ```
    {
        "key": "string"
    }
    ```
    """

    pass


class PasswordResetConfirmView(RestAuthPasswordResetConfirmView):
    """
    This is the endpoint that the client POSTS to after having recieved
    the "rest_confirm_password" view.
    Takes the following parameters:
    ```
    {
        "key": "string",
        "uid": "string"
    }
    ```
    """

    pass


class PasswordChangeView(RestAuthPasswordChangeView):
    """
    Calls Django Auth SetPasswordForm save method.
    """

    pass


class PasswordResetView(RestAuthPasswordResetView):
    """
    Calls Django Auth PasswordResetForm save method.
    """

    pass
