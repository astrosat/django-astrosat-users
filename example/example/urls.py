from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from rest_framework.routers import SimpleRouter
from rest_framework_swagger.views import get_swagger_view

from astrosat.urls import (
    urlpatterns as astrosat_urlpatterns,
    api_urlpatterns as astrosat_api_urlpatterns,
)

from astrosat_users.urls import (
    urlpatterns as astrosat_users_urlpatterns,
    api_urlpatterns as astrosat_users_api_urlpatterns,
)

from .views import index_view


admin.site.site_header = "Admin for Example Project for Django-Astrosat-Users"

handler400 = "astrosat.views.handler400"
handler403 = "astrosat.views.handler403"
handler404 = "astrosat.views.handler404"
handler500 = "astrosat.views.handler500"


##############
# api routes #
##############

api_router = SimpleRouter()
api_urlpatterns = [
    path("", include(api_router.urls)),
    path(
        "swagger/", get_swagger_view(title="Django-Astrosat-Users API"), name="swagger"
    ),
]
api_urlpatterns += astrosat_api_urlpatterns
api_urlpatterns += astrosat_users_api_urlpatterns


#################
# normal routes #
#################

urlpatterns = [
    # admin...
    path("admin/", admin.site.urls),
    # API...
    path("api/", include(api_urlpatterns)),
    # astrosat...
    path("astrosat/", include(astrosat_urlpatterns)),
    # astrosat_users...
    path("astrosat_users/", include(astrosat_users_urlpatterns)),
    # index...
    path("", index_view, name="index"),
]

if settings.DEBUG:

    # allow the error pages to be accessed during development...

    from functools import (
        partial,
    )  # (using partial to pretend an exception has been raised)
    from django.http import (
        HttpResponseBadRequest,
        HttpResponseForbidden,
        HttpResponseNotFound,
    )
    from astrosat.views import handler400, handler403, handler404, handler500

    urlpatterns += [
        path("400/", partial(handler400, exception=HttpResponseBadRequest())),
        path("403/", partial(handler403, exception=HttpResponseForbidden())),
        path("404/", partial(handler404, exception=HttpResponseNotFound())),
        path(
            "500/", handler500
        ),  # "default_views.server_error" doesn't take an exception
    ]

    # enable django-debug-toolbar during development...

    if "debug_toolbar" in settings.INSTALLED_APPS:

        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
