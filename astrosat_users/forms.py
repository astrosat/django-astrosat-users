from django import forms
from django.contrib.auth import forms as auth_forms
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _

from allauth.account import app_settings as allauth_app_settings
from allauth.account.forms import (
    ResetPasswordForm as AllauthResetPasswordForm,
)
from allauth.account.adapter import get_adapter
from allauth.account.utils import user_pk_to_url_str, url_str_to_user_pk, user_username
from allauth.utils import build_absolute_uri

from .models import User
from .tokens import default_token_generator


###############
# admin forms #
###############


class UserAdminChangeForm(auth_forms.UserChangeForm):

    class Meta(auth_forms.UserChangeForm.Meta):
        model = User


class UserAdminCreationForm(auth_forms.UserCreationForm):

    error_message = auth_forms.UserCreationForm.error_messages.update(
        {
            "duplicate_username": _("This username has already been taken.")
        }
    )

    class Meta(auth_forms.UserCreationForm.Meta):
        model = User

    def clean_username(self):

        username = self.cleaned_data["username"]

        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username

        raise ValidationError(self.error_messages["duplicate_username"])


##############
# user forms #
##############


class UserUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ("name", "description", "roles")


########################################
# special forms to use for validation  #
# w/ allauth and/or rest_auth          #
########################################


class PasswordResetForm(AllauthResetPasswordForm):

    # this class is used by allauth b/c of settings.ACCOUNT_FORMS
    # this class is used by rest_auth b/c of settings.REST_AUTH_SERIALIZERS

    def save(self, request, **kwargs):
        # do everything the same as the parent class,
        # except customize the email message

        adapter = get_adapter(request)
        current_site = get_current_site(request)
        email = self.cleaned_data["email"]
        token_generator = kwargs.get("token_generator", default_token_generator)

        for user in self.users:

            temp_key = token_generator.make_token(user)

            # save it to the password reset model
            # password_reset = PasswordReset(user=user, temp_key=temp_key)
            # password_reset.save()

            if adapter.is_api:
                view_name = "rest_password_reset_confirm"
                user_id = urlsafe_base64_encode(force_bytes(user.pk))
                path = reverse(view_name, kwargs=dict(uid=user_id, token=temp_key))

            else:
                view_name = "account_reset_password_from_key"
                user_id = user_pk_to_url_str(user)
                path = reverse(view_name, kwargs=dict(uidb36=user_id, key=temp_key))

            url = build_absolute_uri(request, path)

            context = {
                "current_site": current_site,
                "user": user,
                "password_reset_url": url,
                "request": request,
            }

            if allauth_app_settings.AUTHENTICATION_METHOD != allauth_app_settings.AuthenticationMethod.EMAIL:
                context['username'] = user_username(user)
            adapter.send_mail('account/email/password_reset_key', email, context)

        return self.cleaned_data["email"]
