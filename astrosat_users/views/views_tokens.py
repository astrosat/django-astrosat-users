from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.exceptions import APIException
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from dj_rest_auth.models import TokenModel
from dj_rest_auth.app_settings import TokenSerializer, create_token

from astrosat_users.conf import app_settings


@api_view(["POST"])
@permission_classes([IsAuthenticated])
# notice how  this uses the standard Django SessionAuthentication instead of the DRF's TokenAuthentication
@authentication_classes([SessionAuthentication])
def token_view(request):
    """
    Used to generate a token for the API from the Backend;
    Given a POST from a user that logged in via the Backend
    creates a new KnoxToken and returns the token key.
    """
    if not app_settings.ASTROSAT_USERS_ENABLE_BACKEND_ACCESS:
        raise APIException(
            "token_view can only be called when ASTROSAT_USERS_ENABLE_BACKEND_ACCESS is set to 'True'"
        )

    try:
        _, token_key = create_token(TokenModel, request.user, TokenSerializer)
    except Exception as e:
        raise APIException(e)

    return Response(token_key)
