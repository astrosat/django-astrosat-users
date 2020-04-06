from itertools import chain
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http.response import HttpResponseNotFound
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, UpdateView
from django.views.generic.base import TemplateView

from astrosat_users.models import User, PROFILES, get_profile_qs


#################
# special views #
#################


class DisabledView(TemplateView):

    template_name = "astrosat_users/disabled.html"


class DisapprovedView(TemplateView):

    template_name = "astrosat_users/disapproved.html"


class UnacceptedView(TemplateView):

    template_name = "astrosat_users/unaccepted.html"

##############
# user views #
##############


@method_decorator(
    login_required(login_url=reverse_lazy("account_login")), name="dispatch"
)
class UserListView(ListView):

    model = User

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(is_active=True)


@method_decorator(
    login_required(login_url=reverse_lazy("account_login")), name="dispatch"
)
class UserDetailView(DetailView):

    model = User
    slug_field = "email"
    slug_url_kwarg = "email"


@method_decorator(
    login_required(login_url=reverse_lazy("account_login")), name="dispatch"
)
class UserUpdateView(UpdateView):
    model = User
    fields = ("name", "description", "roles")
    slug_field = "email"
    slug_url_kwarg = "email"
    template_name_suffix = (
        "_update"
    )  # override stupid default template_name_suffix of "_form"

    def get_object(self, *args, **kwargs):

        obj = super().get_object(*args, **kwargs)

        current_user = self.request.user
        if current_user != obj and not current_user.is_superuser:
            raise PermissionDenied()
        return obj


#################
# profile views #
#################


@method_decorator(
    login_required(login_url=reverse_lazy("account_login")), name="dispatch"
)
class GenericProfileListView(ListView):

    template_name = "astrosat_users/profile_list.html"

    def get_queryset(self):
        return get_profile_qs()


@method_decorator(
    login_required(login_url=reverse_lazy("account_login")), name="dispatch"
)
class GenericProfileDetailView(DetailView):

    template_name = "astrosat_users/profile_detail.html"

    def get_object(self, queryset=None):

        email = self.kwargs.get("email")
        profile_key = self.kwargs.get("profile_key")

        # don't bother calling get_profile_qs...
        # ...I know exactly which profile to return based on the kwargs
        queryset = PROFILES[profile_key].objects.filter(user__email=email)

        try:
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise HttpResponseNotFound(_("No profile found matching the query"))

        return obj


@method_decorator(
    login_required(login_url=reverse_lazy("account_login")), name="dispatch"
)
class GenericProfileUpdateView(UpdateView):

    template_name = "astrosat_users/profile_update.html"
    fields = "__all__"

    def get_object(self, queryset=None):

        email = self.kwargs.get("email")
        profile_key = self.kwargs.get("profile_key")

        # don't bother calling get_profile_qs...
        # ...I know exactly which profile to return based on the kwargs
        queryset = PROFILES[profile_key].objects.filter(user__email=email)

        try:
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise HttpResponseNotFound(_("No profile found matching the query"))

        return obj

    def get_success_url(self):
        obj = self.get_object()
        return reverse_lazy(
            "profile-detail", kwargs={"email": obj.user.email, "profile_key": obj.key}
        )
