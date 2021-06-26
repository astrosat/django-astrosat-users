from functools import partial

from django.urls import include, path, re_path
from django.utils.decorators import method_decorator
from django.urls.resolvers import RegexPattern, RoutePattern

from rest_framework.routers import SimpleRouter

from allauth.urls import urlpatterns as allauth_urlpatterns

from astrosat.decorators import conditional_redirect
from astrosat.routers import SlashlessSimpleRouter

from astrosat_users.conf import app_settings

# backend views...
from .views import text_view, UserListView, UserDetailView, UserUpdateView

# API views...
from .views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetView,
    PasswordResetConfirmView,
    RegisterView,
    VerifyEmailView,
    SendEmailVerificationView,
    UserViewSet,
    MessageViewSet,
    CustomerCreateView,
    CustomerUpdateView,
    CustomerUserListView,
    CustomerUserDetailView,
    CustomerUserInviteView,
    CustomerUserOnboardView,
)

# API views that still authenticate w/ backend...
from .views import token_view

##############
# api routes #
##############

api_router = SlashlessSimpleRouter()
api_router.register("users", UserViewSet, basename="users")
api_router.register(
    "users/(?P<user_id>[^/.]+)/messages", MessageViewSet, basename="messages"
)
api_urlpatterns = [
    path("", include(api_router.urls)),
    path("customers/", CustomerCreateView.as_view(), name="customers-list"),
    path(
        "customers/<slug:customer_id>/",
        CustomerUpdateView.as_view(),
        name="customers-detail"
    ),
    path(
        "customers/<slug:customer_id>/users/",
        CustomerUserListView.as_view(),
        name="customer-users-list",
    ),
    path(
        "customers/<slug:customer_id>/users/<slug:user_id>/",
        CustomerUserDetailView.as_view(),
        name="customer-users-detail",
    ),
    path(
        "customers/<slug:customer_id>/users/<slug:user_id>/invite/",
        CustomerUserInviteView.as_view(),
        name="customer-users-invite",
    ),
    path(
        "customers/<slug:customer_id>/users/<slug:user_id>/onboard/",
        CustomerUserOnboardView.as_view(),
        name="customer-users-onboard",
    ),
    # overwrite the rest_auth.urls to cope w/ the idiosyncracies of astrosat_users
    # (and to exclude the built-in user ViewSets)
    # path("authentication/", include("dj_rest_auth.urls")),
    # path("authentication/registration/", include("dj_rest_auth.registration.urls")),
    path("authentication/login/", LoginView.as_view(), name="rest_login"),
    path("authentication/logout/", LogoutView.as_view(), name="rest_logout"),
    path(
        "authentication/password/change/",
        PasswordChangeView.as_view(),
        name="rest_password_change",
    ),
    path(
        "authentication/password/reset/",
        PasswordResetView.as_view(),
        name="rest_password_reset",
    ),
    path(
        "authentication/password/verify-reset/",
        PasswordResetConfirmView.as_view(),
        name="rest_password_reset_confirm",
    ),
    # a "special" api_urlpattern that authenticates using django-allauth NOT django-rest-auth
    path(
        "authentication/registration/",
        RegisterView.as_view(),
        name="rest_register"
    ),
    path(
        "authentication/registration/verify-email/",
        VerifyEmailView.as_view(),
        name="rest_verify_email",
    ),
    path(
        "authentication/send-email-verification/",
        SendEmailVerificationView.as_view(),
        name="rest_send_email_verification",
    ),
    path("token", token_view, name="token"),
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

# ensure that all the urlpatterns provided by allauth use the "check_backend_access" decorator
conditional_backend_url_patterns = []
for urlresolver in allauth_urlpatterns:
    for urlpattern in urlresolver.url_patterns:

        if isinstance(urlpattern.pattern, RegexPattern):
            pattern_fn = re_path
        elif isinstance(urlpattern.pattern, RoutePattern):
            pattern_fn = path
        else:
            raise NotImplementedError(
                f"unable to decode pattern {urlpattern.pattern}"
            )

        conditional_backend_url_patterns.append(
            pattern_fn(
                str(urlpattern.pattern),
                check_backend_access(urlpattern.callback),
                name=urlpattern.name,
            )
        )

urlpatterns = [
    # allauth stuff...
    path("authentication/", include(conditional_backend_url_patterns)),
    path(
        "authentication/text/disabled/",
        partial(text_view, text="Backend access is currently disabled."),
        name="disabled",
    ),
    # user stuff...
    path(
        "users/",
        check_backend_access(UserListView.as_view()),
        name="user-list"
    ),
    path(
        "users/<slug:id>/",
        check_backend_access(UserDetailView.as_view()),
        name="user-detail",
    ),
    path(
        "users/<slug:id>/update/",
        check_backend_access(UserUpdateView.as_view()),
        name="user-update",
    ),
]
