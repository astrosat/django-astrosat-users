from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.utils.translation import ugettext_lazy as _

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from allauth.account import app_settings as allauth_settings
from allauth.exceptions import ImmediateHttpResponse
from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress, EmailConfirmation, EmailConfirmationHMAC
from allauth.account.utils import complete_signup, send_email_confirmation
from allauth.account.views import ConfirmEmailView

from rest_auth.registration.views import (
    RegisterView as RestAuthRegsiterView,
    LoginView as RestAuthLoginView,
)
from rest_auth.app_settings import TokenSerializer, JWTSerializer, create_token

from astrosat.decorators import conditional_redirect

from .models import User
from .serializers import UserSerializer, RestRegisterSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer
from .conf import app_settings


class IsAdminOrOwner(BasePermission):

    def has_object_permission(self, request, view, obj):
        # anybody can do GET, HEAD, or OPTIONS
        if request.method in SAFE_METHODS:
            return True

        # only the admin or the specific user can do POST, PUT, PATCH, DELETE
        user = request.user
        return user.is_superuser or user == obj


# rest_auth does a pretty good job of mapping to allauth
# however, I configure allauth using a combination of adapters & app_settings
# and rest_auth isn't always generic enough to cope w/ that
# so I have overloaded some of the view classes here


@api_view(["GET", "POST"])
def rest_disabled(request, *args, **kwargs):

    return Response({
        "detail": "We are sorry, but the sign up is currently closed."
    })


@api_view(["GET"])
def rest_confirm_email(request, key):

    # TODO: AGAIN, MOVE THIS TO adapter
    confirmation = EmailConfirmationHMAC.from_key(key)
    if not confirmation:
        qs = EmailConfirmation.objects.all_valid()
        qs = qs.select_related("email_address__user")
        try:
            confirmation = qs.get(key=key.lower())
        except EmailConfirmation.DoesNotExist:
            raise APIException(f"{key} is an invalid email verification key.")

    detail = None
    email_address = confirmation.confirm(request)
    if email_address:
        detail = "successfully confirmed email address."

    # do not login on confirmation, that's a security risk, just response w/ a confirmation messsage
    return Response({"detail": detail})


@method_decorator(sensitive_post_parameters("password1", "password2"), name="dispatch")
@method_decorator(conditional_redirect(lambda: not app_settings.ASTROSAT_USERS_ALLOW_REGISTRATION, redirect_name="rest_disabled"), name="dispatch")
class RegisterView(RestAuthRegsiterView):

    serializer_class = RestRegisterSerializer

    def get_response_data(self, user):
        # need to make sure that
        if app_settings.ASTROSAT_USERS_REQUIRE_VERIFICATION:
            return {"detail": _("Verification e-mail sent.")}

        if getattr(settings, 'REST_USE_JWT', False):
            data = {
                'user': user,
                'token': self.token
            }
            return JWTSerializer(data).data
        else:
            return TokenSerializer(user.auth_token).data

    def perform_create(self, serializer):

        user = serializer.save(self.request)
        if getattr(settings, 'REST_USE_JWT', False):
            self.token = jwt_encode(user)
        else:
            create_token(self.token_model, user, serializer)

        if app_settings.ASTROSAT_USERS_REQUIRE_VERIFICATION:
            email_verification = allauth_settings.EmailVerificationMethod.MANDATORY
        else:
            email_verification = allauth_settings.EmailVerificationMethod.NONE

        complete_signup(self.request, user, email_verification, None)

        return user


class LoginView(RestAuthLoginView):

    def login(self):

        self.user = self.serializer.validated_data['user']

        primary_user_emailaddress = self.user.emailaddress_set.get(primary=True)

        if getattr(settings, 'REST_USE_JWT', False):
            self.token = jwt_encode(self.user)
        else:
            self.token = create_token(self.token_model, self.user, self.serializer)

        # just like the login adapter, I need to add some checks here
        # TODO: MOVE THIS INTO A GENERIC ADAPTER METHOD (THAT CHECKS @is_api)
        if app_settings.ASTROSAT_USERS_REQUIRE_VERIFICATION and not self.user.is_verified:
            send_email_confirmation(self.request, self.user, signup=False)
            response = Response(
                {
                    "detail": f"""We have sent an e-mail to {primary_user_emailaddress } for verification.
		                Follow the link provided to finalize the signup process.
		                Please contact us if you do not receive it within a few minutes."""
                },
                status=status.HTTP_200_OK
            )
            raise ImmediateHttpResponse(response)

        if app_settings.ASTROSAT_USERS_REQUIRE_APPROVAL and not self.user.is_approved:
            response = Response(
                {
                    "detail": f"The account {self.user} has not yet been approved."
                },
                status=status.HTTP_200_OK
            )
            raise ImmediateHttpResponse(response)

        if getattr(settings, 'REST_SESSION_LOGIN', True):
            self.process_login()

    def post(self, request, *args, **kwargs):

        self.request = request
        self.serializer = self.get_serializer(data=self.request.data, context={'request': request})
        self.serializer.is_valid(raise_exception=True)

        try:
            self.login()
        except ImmediateHttpResponse as e:
            return e.response

        return self.get_response()


class UserViewSet(ModelViewSet):

    permission_classes = [IsAuthenticated, IsAdminOrOwner]
    queryset = User.objects.active()
    serializer_class = UserSerializer
    lookup_field = "username"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # TODO: ADD SOME LOGIC HERE TO RESTRICT WHICH PROFILES WE CAN SERIALIZE
        # TODO: (NOT ALL USERS CAN MODIFY ALL PROFILES)
        managed_profiles = [
            profile_key
            for profile_key in User.profile_keys
        ]

        context.update({
            "managed_profiles": managed_profiles
        })
        return context
