import itertools
import re
from typing import Any

from urllib.parse import urljoin

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import resolve, reverse

from rest_framework.exceptions import APIException

from allauth.account import app_settings as allauth_app_settings
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.forms import default_token_generator
from allauth.account.utils import (
    complete_signup,
    send_email_confirmation,
    user_pk_to_url_str,
    url_str_to_user_pk,
    user_email,
    user_username,
)

from allauth.account.utils import user_username
from allauth.exceptions import ImmediateHttpResponse
from allauth.utils import build_absolute_uri

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from astrosat_users.conf import app_settings
from astrosat_users.serializers import UserSerializerLite
from astrosat_users.utils import rest_encode_user_pk

UserModel = get_user_model()


class AdapterMixin(object):
    @property
    def is_api(self):
        return re.match("^/api/", self.request.path) is not None

    def is_open_for_signup(self, request: HttpRequest):
        return app_settings.ASTROSAT_USERS_ALLOW_REGISTRATION

    def check_user(self, user, **kwargs):
        """
        Here is where I put all the custom checks that I want to happen
        which aren't necessarily form/serializer errors.
        """

        from astrosat_users.views.views_text import text_view

        # verification (overriding the check here in order to not automatically resend the verification email)
        if (
            kwargs.get("check_verification", True) and
            app_settings.ASTROSAT_USERS_REQUIRE_VERIFICATION and
            not user.is_verified
        ):
            msg = f"User {user} is not verified."
            # send_email_confirmation(request, user)
            if self.is_api:
                raise APIException(msg)
            else:
                response = self.respond_email_verification_sent(
                    self.request, user
                )
                raise ImmediateHttpResponse(response)

        # approval (display a message)
        if (
            kwargs.get("check_approval", True) and
            app_settings.ASTROSAT_USERS_REQUIRE_APPROVAL and
            not user.is_approved
        ):
            msg = f"User {user} has not been approved."
            if self.is_api:
                raise APIException(msg)
            else:
                # (this is dealt w/ in "authenticate" below as a ValidationError, but just-in-case...)
                response = text_view(self.request, text=msg)
                raise ImmediateHttpResponse(response)

        # terms acceptance (display a message)
        if (
            kwargs.get("check_terms_acceptance", True) and
            app_settings.ASTROSAT_USERS_REQUIRE_TERMS_ACCEPTANCE and
            not user.accepted_terms
        ):
            msg = f"User {user} has not yet accepted the terms & conditions."
            if self.is_api:
                raise APIException(msg)
            else:
                # (this is dealt w/ in "authenticate" below as a ValidationError, but just-in-case...)
                response = text_view(self.request, text=msg)
                raise ImmediateHttpResponse(response)

        # change_password (redirecting to reset_password_view)
        if kwargs.get("check_password", True) and user.change_password:
            self.send_password_confirmation_email(user, user.email)
            if self.is_api:
                raise APIException("A password reset email has been sent.")
            else:
                response = redirect("account_reset_password_done")
                raise ImmediateHttpResponse(response)

        return True


class AccountAdapter(AdapterMixin, DefaultAccountAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_token_generator = default_token_generator

    def authenticate(self, request: HttpRequest, **credentials):
        user = super().authenticate(request, **credentials)

        if user is not None:
            if app_settings.ASTROSAT_USERS_REQUIRE_APPROVAL and not user.is_approved:
                msg = f"User {user} has not been approved."
                raise forms.ValidationError(msg)
            elif (
                app_settings.ASTROSAT_USERS_REQUIRE_TERMS_ACCEPTANCE and
                not user.accepted_terms
            ):
                msg = f"User {user} has not yet accepted Terms & Conditions."
                raise forms.ValidationError(msg)

        return user

    def get_login_url(self, request):
        """Constructs the login url.
        """
        if self.is_api:
            # if the user registered via the API, then get the URL that the client should use
            path = app_settings.ACCOUNT_LOGIN_CLIENT_URL
        else:
            # otherwise, just use the builtin allauth view
            path = reverse("account_signup")
        if self.is_api and "HTTP_ORIGIN" in request.META:
            # request originates from a client on a different domain...
            url = urljoin(request.META['HTTP_ORIGIN'], path)
        else:
            url = build_absolute_uri(request, path)
        return url

    def get_email_confirmation_url(self, request, emailconfirmation):
        """Constructs the email confirmation (activation) url.
        Note that if you have architected your system such that email
        confirmations are sent outside of the request context `request`
        can be `None` here.
        """
        if self.is_api:
            # if the user registered via the API, then get the URL that the client should use
            path = app_settings.ACCOUNT_CONFIRM_EMAIL_CLIENT_URL.format(
                key=emailconfirmation.key
            )
        else:
            # otherwise, just use the builtin allauth view
            path = reverse(
                "account_confirm_email", args=[emailconfirmation.key]
            )

        if self.is_api and "HTTP_ORIGIN" in request.META:
            # request originates from a client on a different domain...
            url = urljoin(request.META['HTTP_ORIGIN'], path)
        else:
            url = build_absolute_uri(request, path)
        return url

    def get_password_confirmation_url(self, request, user, token=None):
        """Constructs the password confirmation (reset) url.
        """

        token_key = (
            self.default_token_generator.make_token(user)
            if token is None else token
        )

        if self.is_api:
            # TODO: ASK MARK WHAT THIS SHOULD BE?!?
            path = app_settings.ACCOUNT_CONFIRM_PASSWORD_CLIENT_URL.format(
                key=token_key, uid=rest_encode_user_pk(user)
            )

        else:
            path = reverse(
                "account_reset_password_from_key",
                kwargs={
                    "key": token_key, "uidb36": user_pk_to_url_str(user)
                },
            )

        if self.is_api and "HTTP_ORIGIN" in request.META:
            # request originates from a client on a different domain...
            url = urljoin(request.META['HTTP_ORIGIN'], path)
        else:
            url = build_absolute_uri(request, path)
        return url

    def login(self, request, user):

        # THIS IS F%!&@#G CONFUSING...
        # This fn gets called from "allauth.utils.perform_login" which assumes
        # that login succeeds (b/c "perform_login" already has its own checks);
        # so if I just try to return an HttpResponse, rather than actually login,
        # an error will ocurr b/c the _next_ thing that "perform_login" does is to
        # redirect to LOGIN_REDIRECT_URL which asserts that the user is authenticated.
        # However, there is a try-catch block in "perform_login" which immediately returns
        # a response in case "ImmediateHttpResponse" is thrown.  I thought that adding the
        # "check_user()" method to LoginForm & LoginSerializer handled this.  But it turns
        # out that I need to deal w/ this during Registration as well.  I am not happy.
        # TODO: GET RID OF THIS FN !

        try:

            self.check_user(
                user,
                check_verification=app_settings.
                ASTROSAT_USERS_REQUIRE_VERIFICATION,
                check_approval=app_settings.ASTROSAT_USERS_REQUIRE_APPROVAL,
                check_terms_acceptance=app_settings.
                ASTROSAT_USERS_REQUIRE_TERMS_ACCEPTANCE,
                check_password=False,
            )
        except APIException:
            # the LoginSerializer calls adapter.check_user explicitly so will prevent
            # logins there; There's no need to prevent RegisterSerializer from proceeding
            # if these checks fail since I don't automatically log the user in after registration
            pass
        except ImmediateHttpResponse:
            raise

        return super().login(request, user)

    def populate_username(self, request, user):
        """
        Fills in a valid username, if missing.  If the username
        is already present it is assumed to be valid.  In astrosat,
        we simply use the email address as the username.
        """
        email = user_email(user)
        username = user_username(user)
        if allauth_app_settings.USER_MODEL_USERNAME_FIELD:
            # the original code does some fancy logic to generate a unique username
            # this code just uses either the value explicitly passed by the fronted
            # or defaults to the email address
            user_username(user, username or email)

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
        Saves a new User instance from the signup form / serializer.
        Overriding to add extra fields and send a notification email.
        Overriding this Adapter method instead of using signals,
        so that the notification is only sent when a user is added
        by the form/serializer (as opposed to in the shell or via the admin).
        """
        saved_user = super().save_user(request, user, form, commit=commit)

        extra_fields = ["accepted_terms", "registration_stage", "name"]
        for extra_field in extra_fields:
            if extra_field in form.cleaned_data:
                setattr(saved_user, extra_field, form.cleaned_data[extra_field])
        if commit:
            saved_user.save()

        # if commit and app_settings.ASTROSAT_USERS_NOTIFY_SIGNUPS:
        #     subject = super(
        #     ).format_email_subject(f"new user signup: {saved_user}")
        #     message = f"User {saved_user.email} signed up for an account."
        #     mail_managers(subject, message, fail_silently=True)
        return saved_user

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """
        Sends the actual email verification message.
        After doing this the normal way, records the key that was used in that message.
        """
        super().send_confirmation_mail(request, emailconfirmation, signup)

        user = emailconfirmation.email_address.user
        user.latest_confirmation_key = emailconfirmation.key
        user.save()

    def send_password_confirmation_email(self, user, email, **kwargs):

        token_generator = kwargs.get(
            "token_generator", self.default_token_generator
        )
        token_key = token_generator.make_token(user)

        url = self.get_password_confirmation_url(self.request, user, token_key)

        template_prefix = kwargs.get(
            "template_prefix", "account/email/password_reset_key"
        )
        context = kwargs.get("context", {})
        context.update({
            "current_site": get_current_site(self.request),
            "user": user,
            "password_reset_url": url,
            "request": self.request,
        })

        if (
            allauth_app_settings.AUTHENTICATION_METHOD !=
            allauth_app_settings.AuthenticationMethod.EMAIL
        ):
            context["username"] = user_username(user)

        self.send_mail(template_prefix, email, context)

    def send_mail(self, template_prefix, email, context, **kwargs):
        cc = kwargs.pop("cc", [])
        bcc = kwargs.pop("bcc", [])
        if cc:
            if isinstance(cc, str):
                raise TypeError('"cc" argument must be a list or tuple')
            cc = list(cc)
        if bcc:
            if isinstance(bcc, str):
                raise TypeError('"bcc" argument must be a list or tuple')
            self.bcc = list(bcc)
        msg = self.render_mail(template_prefix, email, context)
        msg.cc = [address for address in cc if address != email]
        msg.bcc = [address for address in bcc if address != email]
        msg.send(fail_silently=kwargs.pop("fail_silently", False))

        if kwargs.pop("save_message", True):
            for address in itertools.chain(msg.to, msg.cc, msg.bcc):
                try:
                    user = UserModel.objects.get(email=address)
                    user.add_message(
                        title=msg.subject,
                        sender=msg.from_email,
                        content=msg.body,
                    )
                except ObjectDoesNotExist:
                    pass
        return msg

    def set_password(self, user, password):
        user.set_password(password)
        user.change_password = False
        user.save()


class SocialAccountAdapter(AdapterMixin, DefaultSocialAccountAdapter):
    pass
