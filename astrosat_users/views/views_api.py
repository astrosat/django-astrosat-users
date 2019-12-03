from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_auth.app_settings import TokenSerializer

from astrosat_users.serializers import UserSerializer


@api_view(["GET", "POST"])
def api_disabled(request, *args, **kwargs):
    content = {"detail": "We are sorry, but the sign up is currently closed."}
    return Response(content)


@api_view(["GET", "POST"])
def api_unused(request, *args, **kwargs):
    raise APIException("This view is unused")
