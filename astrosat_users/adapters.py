import re
from typing import Any

from django.core.mail import mail_managers
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import resolve_url
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode as uid_encode

from allauth.exceptions import ImmediateHttpResponse
from allauth.utils import build_absolute_uri
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.forms import default_token_generator
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import (
    complete_signup,
    send_email_confirmation,
    user_pk_to_url_str,
    url_str_to_user_pk,
    user_username,
)

from .conf import app_settings
from .utils import rest_encode_user_pk


class AccountAdapter(DefaultAccountAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_token_generator = default_token_generator

    @property
    def is_api(self):
        return re.match("^/api/", self.request.path) is not None

    def is_open_for_signup(self, request: HttpRequest):
        return app_settings.ASTROSAT_USERS_ALLOW_REGISTRATION

    # TODO: MOVE THIS LOGIC TO THE LoginForm, WHERE IT BELONGS !
    def login(self, request, user):
        """
        Adds some checks into the login procedure.
        """

        # THIS IS F%!&@#G CONFUSING...
        # "astrosat_users.adapters.login" gets called from "allauth.utils.perform_login" which assumes
        # that login succeeds (b/c "perform_login" already has its own checks); so if I just try to return
        # an HttpResponse, rather than actually login, an error will ocurr b/c the _next_ thing that "perform_login"
        # does is to redirect to LOGIN_REDIRECT_URL and the assert in "astrosat_users.adapters.get_login_redirect_url"
        # will fail (fwiw, that assert is in the base class as well).  However, there _is_ a try-catch block in
        # "perform_login" which immediately returns a response in case an "allauth.exceptions.ImmediateHttpResponse"
        # is caught.  So, if a check fails I just raise an ImmediateHttpResponse w/ the correct response.

        if app_settings.ASTROSAT_USERS_REQUIRE_VERIFICATION and not user.is_verified:
            send_email_confirmation(request, user)
            response = self.respond_email_verification_sent(request, user)
            raise ImmediateHttpResponse(response)

        if app_settings.ASTROSAT_USERS_REQUIRE_APPROVAL and not user.is_approved:
            request.session["username"] = user.username
            response = HttpResponseRedirect(reverse("disapproved"))
            raise ImmediateHttpResponse(response)

        super().login(request, user)

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """
        Sends the actual email verification message.
        After doing this the normal way, records the key that was used in that message.
        """
        super().send_confirmation_mail(request, emailconfirmation, signup)

        user = emailconfirmation.email_address.user
        user.latest_confirmation_key = emailconfirmation.key
        user.save()

    def get_email_confirmation_url(self, request, emailconfirmation):
        """Constructs the email confirmation (activation) url.
        Note that if you have architected your system such that email
        confirmations are sent outside of the request context `request`
        can be `None` here.
        """
        if self.is_api:
            # TODO: ASK MARK WHAT THIS SHOULD BE?!?
            path = app_settings.ACCOUNT_CONFIRM_EMAIL_CLIENT_URL.format(
                key=emailconfirmation.key
            )
        else:
            path = reverse("account_confirm_email", args=[emailconfirmation.key])

        url = build_absolute_uri(request, path)
        return url

    def get_password_confirmation_url(self, request, user, token=None):
        """Constructs the password confirmation (reset) url.
        """

        token_key = (
            self.default_token_generator.make_token(user) if token is None else token
        )

        if self.is_api:
            # TODO: ASK MARK WHAT THIS SHOULD BE?!?
            path = app_settings.ACCOUNT_CONFIRM_PASSWORD_CLIENT_URL.format(
                key=token_key, uid=rest_encode_user_pk(user)
            )

        else:
            path = reverse(
                "account_reset_password_from_key",
                kwargs={"key": token_key, "uidb36": user_pk_to_url_str(user)},
            )

        url = build_absolute_uri(request, path)
        return url

    def respond_email_verification_sent(self, request, user):
        """
        Adds some context to the default email_verification_sent view.
        Have to do it here, instead of ovewriting the view b/c it is
        (and should remain) an HttpResponseRedirect - which means it has
        no context of it's own.  I overload the session here and access it
        in the "account_email_verification_sent" template.
        """
        user_emailaddress = user.emailaddress_set.get(primary=True)
        request.session["email_recipient"] = user_emailaddress.email

        return super().respond_email_verification_sent(request, user)

    # def clean_password(self, password, user=None):
    # no need to overload this fn
    # django-allauth just hooks into the defined Django Password Validators.
    # astrosat_users must use LengthPasswordValidator & StrengthPasswordValidators.
    # super().clean_password(password, user=user)

    def save_user(self, request, user, form, commit=True):
        """
        Saves a new User instance from the signup form.
        Overriding to send a notification email to the managers.
        Overriding this Adapter method instead of using signals,
        so that the notification is only sent when a user is added
        by the form/serializer (as opposed to in the shell or via the admin).
        """
        saved_user = super().save_user(request, user, form, commit=commit)
        if commit and app_settings.ASTROSAT_USERS_NOTIFY_SIGNUPS:
            subject = super().format_email_subject(f"new user signup: {saved_user}")
            message = f"User {saved_user.email} signed up for an account."
            mail_managers(subject, message, fail_silently=True)
        return saved_user


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest, sociallogin: Any):
        return app_settings.ASTROSAT_USERS_ALLOW_REGISTRATION
