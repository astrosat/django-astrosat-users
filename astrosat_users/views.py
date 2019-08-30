from itertools import chain
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView,  DetailView, UpdateView
from django.views.generic.base import TemplateView

from .conf import app_settings
from .forms import UserUpdateForm
from .models import User
from .profiles import PROFILES, get_profile_qs


#################
# special views #
#################

class DisabledView(TemplateView):

    template_name = "astrosat_users/disabled.html"


class DisapprovedView(TemplateView):

    template_name = "astrosat_users/disapproved.html"


##############
# user views #
##############

class UserListView(ListView):

    model = User

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.active()


@method_decorator(login_required(login_url=reverse_lazy("account_login")), name="dispatch")
class UserDetailView(DetailView):

    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


# TODO: MAKE THIS JUST A NORMAL MODELVIEW?
@method_decorator(login_required(login_url=reverse_lazy("account_login")), name="dispatch")
class UserUpdateView(UpdateView):

    model = User
    slug_field = "username"
    slug_url_kwarg = "username"
    # (UpdateView is based on ModelFormMixin, so I could just specify "fields" here instead of "form_class")
    form_class = UserUpdateForm
    template_name_suffix = '_update'  # override stupid default template_name_suffix of "_form"

    def get_object(self, queryset=None):

        # I specify the lookup keys in the URLConf
        # rather than just updating the request.user
        # technically, I should probably just make this a ModelView
        # ...but I didn't

        queryset = self.get_queryset()

        # try looking up by primary key.
        pk = self.kwargs.get(self.pk_url_kwarg)
        if pk is not None:
            queryset = queryset.filter(pk=pk)

        # try looking up by slug.
        slug = self.kwargs.get(self.slug_url_kwarg)
        if slug is not None and (pk is None or self.query_pk_and_slug):
            slug_field = self.get_slug_field()
            queryset = queryset.filter(**{slug_field: slug})

        # If none of those are defined, it's an error.
        if pk is None and slug is None:
            raise AttributeError("UserUpdateView must be called w/ either pk or slug in URLConf")

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj

    def get_success_url(self):
        obj = self.get_object()
        return reverse_lazy("user-detail", kwargs={"username": obj.username})


#################
# profile views #
#################

# TODO: ABSTRACT THE COMMON FEATURES INTO A BASE CLASS/MIXIN

class GenericProfileListView(ListView):

    template_name = "astrosat_users/profile_list.html"

    def get_queryset(self):
        return get_profile_qs()


@method_decorator(login_required(login_url=reverse_lazy("account_login")), name="dispatch")
class GenericProfileDetailView(DetailView):

    template_name = "astrosat_users/profile_detail.html"

    def get_object(self, queryset=None):

        username = self.kwargs.get("username")
        profile_key = self.kwargs.get("profile_key")

        # don't bother calling get_profile_qs...
        # ...I know exactly which profile to return based on the kwargs
        queryset = PROFILES[profile_key].objects.filter(user__username=username)

        try:
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(_("No profile found matching the query"))

        return obj


@method_decorator(login_required(login_url=reverse_lazy("account_login")), name="dispatch")
class GenericProfileUpdateView(UpdateView):

    fields = "__all__"
    template_name = "astrosat_users/profile_update.html"

    def get_object(self, queryset=None):

        username = self.kwargs.get("username")
        profile_key = self.kwargs.get("profile_key")

        # don't bother calling get_profile_qs...
        # ...I know exactly which profile to return based on the kwargs
        queryset = PROFILES[profile_key].objects.filter(user__username=username)

        try:
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(_("No profile found matching the query"))

        return obj

    def get_success_url(self):
        obj = self.get_object()
        return reverse_lazy("profile-detail", kwargs={"username": obj.user.username, "profile_key": obj.key})
