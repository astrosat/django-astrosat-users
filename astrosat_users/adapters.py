import re
from typing import Any

from django.core.mail import mail_managers
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import resolve_url
from django.urls import reverse

from allauth.exceptions import ImmediateHttpResponse
from allauth.utils import build_absolute_uri
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import complete_signup, send_email_confirmation

from .conf import app_settings


class AccountAdapter(DefaultAccountAdapter):
    @property
    def is_api(self):
        return re.match("^/api/", self.request.path) is not None

    def get_login_redirect_url(self, request):
        """
        Returns the default URL to redirect to after logging in.  Note
        that URLs passed explicitly (e.g. by passing along a `next`
        GET parameter) take precedence over the value returned here.
        """
        assert request.user.is_authenticated
        url = app_settings.LOGIN_REDIRECT_URL
        return resolve_url(url)

    def get_logout_redirect_url(self, request):
        """
        Returns the URL to redirect to after the user logs out. Note that
        this method is also invoked if you attempt to log out while no users
        is logged in. Therefore, request.user is not guaranteed to be an
        authenticated user.
        """
        return resolve_url(app_settings.LOGOUT_REDIRECT_URL)

    def get_email_confirmation_redirect_url(self, request):
        """
        The URL to return to after successful e-mail confirmation.
        """
        if request.user.is_authenticated:
            # return app_settings.VERIFICATION_REDIRECT_URL
            return self.get_login_redirect_url(request)
        else:
            return app_settings.VERIFICATION_REDIRECT_URL

    def is_open_for_signup(self, request: HttpRequest):
        return app_settings.ASTROSAT_USERS_ALLOW_REGISTRATION

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

        # if all of the checks passed, then just call the base class login
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
            view_name = "rest_confirm_email"
        else:
            view_name = "account_confirm_email"

        url = reverse(view_name, args=[emailconfirmation.key])
        ret = build_absolute_uri(request, url)
        return ret

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

    def save_user(self, request, user, form, commit=True):
        """
        Saves a new User instance from the signup form.
        Overriding to send a notification email to the managers.
        Overriding this Adapter method instead of using signals,
        so that the notification is only sent when a user is added
        by the form (as opposed to directly on the server or via the admin).
        """
        saved_user = super().save_user(request, user, form, commit=commit)
        if commit and app_settings.ASTROSAT_USERS_NOTIFY_SIGNUPS:
            subject = super().format_email_subject(f"new user signup: {saved_user}")
            message = f"User {saved_user} signed up for an account."
            mail_managers(subject, message, fail_silently=True)
        return saved_user


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest, sociallogin: Any):
        return app_settings.ASTROSAT_USERS_ALLOW_REGISTRATION

    # def get_connect_redirect_url(self, request, socialaccount):
