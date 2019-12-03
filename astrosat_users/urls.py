from django.urls import include, path, re_path
from django.utils.decorators import method_decorator
from django.views.defaults import page_not_found

from rest_framework.exceptions import bad_request
from rest_framework.routers import SimpleRouter

from allauth.urls import urlpatterns as allauth_urlpatterns

# Backend views...

from .views import (
    DisabledView,
    DisapprovedView,
    UserListView,
    UserDetailView,
    UserUpdateView,
    GenericProfileListView,
    GenericProfileDetailView,
    GenericProfileUpdateView,
)

# API views...
from .views import (
    api_disabled,
    LoginView,
    LogoutView,
    RegisterView,
    VerifyEmailView,
    PasswordChangeView,
    PasswordResetView,
    PasswordResetConfirmView,
    UserViewSet,
    UserRoleViewSet,
    UserPermissionViewSet,
)

from astrosat.decorators import conditional_redirect
from .conf import app_settings

##############
# API routes #
##############


api_router = SimpleRouter()
api_router.register("users", UserViewSet, basename="users")
api_router.register("roles", UserRoleViewSet, basename="roles")
api_router.register("permissions", UserPermissionViewSet, basename="permissions")
api_urlpatterns = [
    path("", include(api_router.urls)),
    path("disabled", api_disabled, name="rest_disabled"),
    # overwrite the rest_auth.urls to cope w/ the idiosyncracies of astrosat_users
    # (and to exclude the built-in user ViewSets)
    # path("authentication/", include("rest_auth.urls")),
    # path("authentication/registration/", include("rest_auth.registration.urls")),
    path("authentication/login/", LoginView.as_view(), name="rest_login"),
    path("authentication/logout/", LogoutView.as_view(), name="rest_logout"),
    path("authentication/password/change/", PasswordChangeView.as_view(), name="rest_password_change"),
    path("authentication/password/reset/", PasswordResetView.as_view(), name="rest_password_reset"),
    path("authentication/password/verify-reset/", PasswordResetConfirmView.as_view(), name="rest_password_reset_confirm"),
    path("authentication/registration/", RegisterView.as_view(), name="rest_register"),
    path("authentication/registration/verify-email/", VerifyEmailView.as_view(), name="rest_verify_email",),
]


#################
# normal routes #
#################

# decorator that redirects views to "disabled" if ASTROSAT_USERS_ENABLE_BACKEND_ACCESS is set to False
check_backend_access = method_decorator(
    conditional_redirect(
        lambda: not app_settings.ASTROSAT_USERS_ENABLE_BACKEND_ACCESS,
        redirect_name="disabled",
    ),
    name="dispatch",
)

conditional_backend_url_patterns = [
    # ensures that all the urlpatterns provided by allauth use the "check_backend_access" decorator defined in "astrosat_users.views"
    re_path(
        urlpattern.pattern,
        check_backend_access(urlpattern.callback),
        name=urlpattern.name,
    )
    for urlresolver in allauth_urlpatterns
    for urlpattern in urlresolver.url_patterns
]


urlpatterns = [
    # allauth stuff...
    path("authentication/", include(conditional_backend_url_patterns)),
    # custom stuff...
    path("authentication/disabled/", DisabledView.as_view(), name="disabled"),
    path("authentication/disapproved/", DisabledView.as_view(), name="disapproved"),
    path("users/", check_backend_access(UserListView.as_view()), name="user-list"),
    path(
        "users/<str:email>/",
        check_backend_access(UserDetailView.as_view()),
        name="user-detail",
    ),
    path(
        "users/<str:email>/update/",
        check_backend_access(UserUpdateView.as_view()),
        name="user-update",
    ),
    path(
        "profiles/",
        check_backend_access(GenericProfileListView.as_view()),
        name="profile-list",
    ),
    path(
        "users/<str:email>/profiles/<slug:profile_key>",
        check_backend_access(GenericProfileDetailView.as_view()),
        name="profile-detail",
    ),
    path(
        "users/<str:email>/profiles/<slug:profile_key>/update/",
        check_backend_access(GenericProfileUpdateView.as_view()),
        name="profile-update",
    ),
]
