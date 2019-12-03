from django.contrib.auth import forms as auth_forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from astrosat_users.models import User


class UserAdminChangeForm(auth_forms.UserChangeForm):
    class Meta(auth_forms.UserChangeForm.Meta):
        model = User


class UserAdminCreationForm(auth_forms.UserCreationForm):

    # email and username are optional fields
    # but they still have to be unique; the clean methods below handle that

    error_message = auth_forms.UserCreationForm.error_messages.update(
        {
            "duplicate_username": _("This username has already been taken."),
            "duplicate_email": _("This email has already been taken."),
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

    def clean_email(self):

        email = self.cleaned_data["email"]

        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email

        raise ValidationError(self.error_messages["duplicate_email"])
