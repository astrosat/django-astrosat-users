from django.conf import settings
from django.urls import re_path
from django.views.generic import TemplateView

from rest_framework.permissions import BasePermission

from drf_yasg.views import get_schema_view
from drf_yasg import openapi


class IsAdminOrDebug(BasePermission):
    def has_object_permission(self, request, view, obj):
        # allow swagger access to anybody in DEBUG mode
        # and only to the admin in all other cases
        user = request.user
        return user.is_superuser or settings.DEBUG


#########
# index #
#########

index_view = TemplateView.as_view(template_name="example/index.html")

###########
# swagger #
###########

api_schema_view = get_schema_view(
    openapi.Info(title="Django-Astrosat-Users API", default_version="v1"),
    public=True,
    permission_classes=(IsAdminOrDebug,),
)

api_schema_views = [
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        api_schema_view.without_ui(cache_timeout=0),
        name="swagger-json",
    ),
    re_path(
        r"^swagger/$",
        api_schema_view.with_ui("swagger", cache_timeout=0),
        name="swagger",
    ),
    re_path(
        r"^redoc/$",
        api_schema_view.with_ui("redoc", cache_timeout=0),
        name="swagger-redoc",
    ),
]
