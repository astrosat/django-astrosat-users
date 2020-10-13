from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from allauth.account import app_settings as allauth_app_settings
from allauth.account.adapter import get_adapter
from allauth.account.forms import (
    LoginForm as AllAuthLoginForm,
    ChangePasswordForm as AllAuthChangePasswordForm,
    SetPasswordForm as AllAuthSetPasswordForm,
    ResetPasswordForm as AllAuthPasswordResetForm,
    SignupForm as AllAuthRegistrationForm,
    EmailAwarePasswordResetTokenGenerator,
)
from allauth.account.utils import user_username, setup_user_email
from allauth.exceptions import ImmediateHttpResponse

from astrosat_users.conf import app_settings
from astrosat_users.models import User


class LoginForm(AllAuthLoginForm):
    def login(self, *args, **kwargs):

        adapter = get_adapter(self.request)
        try:
            # add a few extra checks before calling `perform_login` in the super method
            adapter.check_user(self.user)
        except ImmediateHttpResponse as e:
            return e.response

        return super().login(*args, **kwargs)


class PasswordChangeForm(AllAuthChangePasswordForm):

    pass


class PasswordSetForm(AllAuthSetPasswordForm):

    pass


class PasswordResetForm(AllAuthPasswordResetForm):

    default_token_generator = EmailAwarePasswordResetTokenGenerator()

    def save(self, request, **kwargs):
        # similar to the parent method, except refactored the "send-an-email bit"
        # into the adapter which calls `get_password_confirmation_url` to generate
        # an appropriate url that gets passed to the email template context

        adapter = get_adapter(request)
        email = self.cleaned_data["email"]

        for user in self.users:
            adapter.send_password_confirmation_email(
                user, email, token_generator=self.default_token_generator
            )

        return email


class RegistrationForm(AllAuthRegistrationForm):

    field_order = ["email", "password1", "password2", "requires_customer_registration_completion", "accepted_terms"]

    accepted_terms = forms.BooleanField(label="Accept Terms & Conditions")
    requires_customer_registration_completion = forms.BooleanField(label="User is Registering as part of a Team", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not app_settings.ASTROSAT_USERS_REQUIRE_TERMS_ACCEPTANCE:
            self.fields["accepted_terms"].widget = forms.HiddenInput()
            self.fields["accepted_terms"].required = False

    def clean_accepted_terms(self):
        # just in case the setting changes and the user doesn't clear cache,
        # perform this explicit validation
        accepted_terms = self.cleaned_data["accepted_terms"]
        if app_settings.ASTROSAT_USERS_REQUIRE_TERMS_ACCEPTANCE and not accepted_terms:
            raise forms.ValidationError("Accepting terms & conditions is required.")
        return accepted_terms
