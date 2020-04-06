from django import forms
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from allauth.account import app_settings as allauth_app_settings
from allauth.account.adapter import get_adapter
from allauth.account.forms import (
    LoginForm as AllAuthLoginForm,
    ResetPasswordForm as AllAuthPasswordResetForm,
    SignupForm as AllAuthRegistrationForm,
    EmailAwarePasswordResetTokenGenerator,
)
from allauth.account.utils import user_username

from astrosat_users.conf import app_settings
from astrosat_users.models import User


class LoginForm(AllAuthLoginForm):

    # TODO: SHOULD I MOVE VALIDATION INTO THIS CLASS AS W/ LoginSerializer ?
    # TODO: CONCEPTUALLY, THAT'S THE RIGHT PLACE (& IT WOULD MAKE AccountAdapter.login CLEANER)
    # TODO: BUT USING THE ADAPTER LETS ME REDIRECT TO ANOTHER PAGE, WHICH IS NICE.
    pass


class PasswordResetForm(AllAuthPasswordResetForm):

    # The "reset password" view sends a confirmation email just like the
    # "registration" view; for the backend this just works, for the API I
    # have had to overload some fns to work out what the clickable link in
    # that email should be (I have added get_password_confirmation_url to
    # "adapters" in order to compute that)

    default_token_generator = EmailAwarePasswordResetTokenGenerator()

    def save(self, request, **kwargs):
        # just like the parent method
        # except calls get_password_confirmation_url to generate the url
        # passed to the email template context

        current_site = get_current_site(request)
        adapter = get_adapter(request)
        email = self.cleaned_data["email"]
        token_generator = kwargs.get("token_generator", self.default_token_generator)

        for user in self.users:

            token_key = token_generator.make_token(user)

            url = adapter.get_password_confirmation_url(request, user, token_key)

            context = {
                "current_site": current_site,
                "user": user,
                "password_reset_url": url,
                "request": request,
            }

            if (
                allauth_app_settings.AUTHENTICATION_METHOD
                != allauth_app_settings.AuthenticationMethod.EMAIL
            ):
                context["username"] = user_username(user)
            adapter.send_mail("account/email/password_reset_key", email, context)

        return self.cleaned_data["email"]


class RegistrationForm(AllAuthRegistrationForm):

    field_order = ["email", "password1", "password2", "has_accepted_terms"]

    has_accepted_terms  = forms.BooleanField(required=app_settings.ASTROSAT_USERS_REQUIRE_TERMS_ACCEPTANCE, label="Accept Terms & Conditions")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not app_settings.ASTROSAT_USERS_REQUIRE_TERMS_ACCEPTANCE:
            self.fields["has_accepted_terms"].widget = forms.HiddenInput()

    def clean_has_accepted_terms(self):
        # just in case the setting changes and the user doesn't clear cache,
        # perform this explicit validation
        has_accepted_terms = self.cleaned_data["has_accepted_terms"]
        if app_settings.ASTROSAT_USERS_REQUIRE_TERMS_ACCEPTANCE and not has_accepted_terms:
            raise forms.ValidationError("Accepting terms & conditions is required.")
        return has_accepted_terms
