from collections import OrderedDict

from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response

from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema

from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import get_adapter
from allauth.account.utils import complete_signup, send_email_confirmation
from allauth.exceptions import ImmediateHttpResponse

from dj_rest_auth.views import (
    LoginView as RestAuthLoginView,
    LogoutView as RestAuthLogoutView,
    PasswordChangeView as RestAuthPasswordChangeView,
    PasswordResetView as RestAuthPasswordResetView,
    PasswordResetConfirmView as RestAuthPasswordResetConfirmView,
)
from dj_rest_auth.registration.views import (
    RegisterView as RestAuthRegisterView,
    VerifyEmailView as RestAuthVerifyEmailView,
)

from astrosat_users.conf import app_settings as astrosat_users_settings
from astrosat_users.models.models_users import UserRegistrationStageType
from astrosat_users.serializers import (
    UserSerializerLite,
    KnoxTokenSerializer,
    VerifyEmailSerializer,
    SendEmailVerificationSerializer,
)
from astrosat_users.utils import create_knox_token

REGISTRATION_CLOSED_MSG = _(
    "We are sorry, but the sign up is currently closed."
)

###############
# permissions #
###############


class IsNotAuthenticated(BasePermission):
    def has_permission(self, request, view):
        # anybody can do GET, HEAD, or OPTIONS
        if request.method in SAFE_METHODS:
            return True

        # only an unauthenticated user can do POST, PUT, PATCH, DELETE
        user = request.user
        return not user.is_authenticated


class AllowRegistrationPermission(BasePermission):
    def has_permission(self, request, view):
        if not astrosat_users_settings.ASTROSAT_USERS_ALLOW_REGISTRATION:
            # raising an error instead of returning False in order to get a custom message
            # as per https://github.com/encode/django-rest-framework/issues/3754#issuecomment-206953020
            raise PermissionDenied(REGISTRATION_CLOSED_MSG)
        return True


#################
# swagger stuff #
#################

# b/c ACCOUNT_USERNAME_REQURED is False and ACCOUNT_EMAIL_REQUIRED is True, not all fields
# from the LoginSerializer/RegisterSerializer are used in the LoginView/RegisterView
# therefore, I overide the swagger documentation w/ the following schemas...

_login_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties=OrderedDict((
        # ("username", openapi.Schema(type=openapi.TYPE_STRING, example="admin")),
        (
            "email",
            openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_EMAIL,
                example="admin@astrosat.net",
            ),
        ),
        (
            "password",
            openapi.Schema(type=openapi.TYPE_STRING, example="password")
        ),
        ("accepted_terms", openapi.Schema(type=openapi.TYPE_BOOLEAN))
    )),
)

_register_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties=OrderedDict((
        (
            "email",
            openapi.Schema(
                type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL
            ),
        ),
        (
            "password1",
            openapi.Schema(type=openapi.TYPE_STRING, example="superpassword23"),
        ),
        (
            "password2",
            openapi.Schema(type=openapi.TYPE_STRING, example="superpassword23"),
        ),
        (
            "customer_name",
            openapi.Schema(type=openapi.TYPE_STRING, example="example company")
        ),
        ("accepted_terms", openapi.Schema(type=openapi.TYPE_BOOLEAN)),
        (
            "registration_stage",
            openapi.Schema(type=openapi.TYPE_STRING, example="CUSTOMER"),
        ),
    )),
)

#########
# views #
#########


@method_decorator(
    swagger_auto_schema(
        request_body=_login_schema,
        responses={status.HTTP_200_OK: KnoxTokenSerializer}
    ),
    name="post",
)
@method_decorator(sensitive_post_parameters("password"), name="dispatch")
class LoginView(RestAuthLoginView):
    """
    Just like rest_auth.LoginView but removes all of the JWT logic
    (no need to override login/save - that is all done in the serializer)
    """

    permission_classes = [IsNotAuthenticated]

    def get_success_response(self):
        # this creates a response based on the KnoxTokenSerializer
        # (and its nested LoginSerializer)
        serializer_class = self.get_response_serializer()
        data = {"user": self.user, "token": self.token}
        serializer = serializer_class(
            instance=data, context={"request": self.request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_error_response(self):
        # this creates a response based on the state of the LoginSerializer
        # (w/ some minimal user info as needed)
        error_details = self.serializer.errors
        if self.serializer.instance is not None:
            user_serializer_lite = UserSerializerLite(
                self.serializer.instance.get("user")
            )
            error_details["user"] = user_serializer_lite.data
        return Response(error_details, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        self.request = request
        self.serializer = self.get_serializer(data=self.request.data)
        # the base class automatically raises an error on an invalid request
        if self.serializer.is_valid():
            self.login()
            return self.get_success_response()
        # but this class manually creates the invalid response
        return self.get_error_response()


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
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        user = serializer.user
        if user.registration_stage == UserRegistrationStageType.ONBOARD:
            user.onboard(adapter=get_adapter(request))
            user.registration_stage = None
            user.save()

        return Response({
            "detail": _("Password has been reset with the new password."),
            "user": UserSerializerLite(user).data
        })


@method_decorator(
    sensitive_post_parameters("password1", "password2"), name="dispatch"
)
@method_decorator(
    swagger_auto_schema(
        request_body=_register_schema,
        responses={status.HTTP_200_OK: UserSerializerLite},
    ),
    name="post",
)
class RegisterView(RestAuthRegisterView):

    permission_classes = [IsNotAuthenticated, AllowRegistrationPermission]

    def get_response_data(self, user):
        # just return a lightweight representation of the user
        # no need to get private details or tokens at this point
        serializer = UserSerializerLite(instance=user)
        return serializer.data

    def perform_create(self, serializer):

        # the RegisterSerializer.save() method eventually calls RegisterSerializer.custom_signup()
        # and - assuming "customer_name" was passed to the view - that creates a customer & customer-user
        user = serializer.save(self.request)

        self.token = create_knox_token(None, user, None)
        complete_signup(
            self.request._request,
            user,
            allauth_settings.EMAIL_VERIFICATION,
            None
        )
        return user


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
    def get_serializer(self, *args, **kwargs):
        # NOTE THAT dj-rest-auth DOESN'T SUPPORT OVERWRITING THIS SERIALIZER, SO I HARD-CODE IT HERE
        return VerifyEmailSerializer(*args, **kwargs)

    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        confirmation = serializer.validated_data["confirmation"]
        confirmation.confirm(self.request)

        # if I have successfuly verified the email address,
        # then I should activate any pending customer_users
        user = serializer.validated_data["user"]
        pending_customer_users_qs = user.customer_users.pending()
        pending_customer_users_qs.update(customer_user_status="ACTIVE")

        response = {
            "detail":
                _("ok"),
            "user":
                UserSerializerLite(instance=serializer.validated_data["user"]
                                  ).data,
        }

        return Response(response, status=status.HTTP_200_OK)


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

        user = serializer.validated_data["user"]

        if not user.is_verified:
            send_email_confirmation(request, user)
            msg = _("Verification email sent.")
        else:
            msg = _(f"No verification email sent; {user} is already verified.")

        return Response({"detail": msg})
