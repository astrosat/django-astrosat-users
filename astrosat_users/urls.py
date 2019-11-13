from django.urls import include, path, re_path
from django.utils.decorators import method_decorator
from rest_framework.routers import SimpleRouter

from allauth.urls import urlpatterns as allauth_urlpatterns
from rest_auth.views import PasswordResetConfirmView

from astrosat.decorators import conditional_redirect

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

from .views_api import (
    rest_confirm_email,
    rest_disabled,
    RegisterView,
    LoginView,
    UserViewSet,
    UserRoleViewSet,
    UserPermissionViewSet,
)
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
    path("rest-auth/disabled/", rest_disabled, name="rest_disabled"),
    # overwrite some of the rest_auth.urls to cope w/ the idiosyncrasies of astrosat_users
    path("rest-auth/login/", LoginView.as_view(), name="rest_login"),
    path("rest-auth/registration/", RegisterView.as_view(), name="rest_register"),
    re_path(
        r"^rest-auth/password/reset/(?P<uid>[0-9A-Za-z]+)-(?P<token>.+)/$",
        PasswordResetConfirmView.as_view(),
        name="rest_password_reset_confirm",
    ),
    # # path("rest-auth/verify-email/", RestVerifyEmailView.as_view(), name='rest_verify_email'),
    path(
        "rest-auth/confirm-email/<key>/", rest_confirm_email, name="rest_confirm_email"
    ),
    # and now include the built-in urls
    path("rest-auth/", include("rest_auth.urls")),
    path("rest-auth/registration/", include("rest_auth.registration.urls")),
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
    path("accounts/disabled/", DisabledView.as_view(), name="disabled"),
    # allauth stuff...
    path("accounts/", include(conditional_backend_url_patterns)),
    path(
        "accounts/disapproved/",
        check_backend_access(DisapprovedView.as_view()),
        name="disapproved",
    ),
    # custom stuff...
    path(
        "accounts/users/",
        check_backend_access(UserListView.as_view()),
        name="user-list",
    ),
    path(
        "accounts/users/<str:username>/",
        check_backend_access(UserDetailView.as_view()),
        name="user-detail",
    ),
    path(
        "accounts/users/<str:username>/update/",
        check_backend_access(UserUpdateView.as_view()),
        name="user-update",
    ),
    path(
        "accounts/profiles/",
        check_backend_access(GenericProfileListView.as_view()),
        name="profile-list",
    ),
    path(
        "accounts/users/<str:username>/profiles/<slug:profile_key>",
        check_backend_access(GenericProfileDetailView.as_view()),
        name="profile-detail",
    ),
    path(
        "accounts/users/<str:username>/profiles/<slug:profile_key>/update/",
        check_backend_access(GenericProfileUpdateView.as_view()),
        name="profile-update",
    ),
]
