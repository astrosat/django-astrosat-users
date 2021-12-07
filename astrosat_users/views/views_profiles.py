from collections import OrderedDict

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property

from rest_framework import generics, serializers, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated, BasePermission

from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema

from astrosat.decorators import swagger_fake


class NoMatchingProfileException(APIException):
    status_code = 400
    default_detail = "Unable to find a profile for the given user"
    default_code = "no_matching_profile"


class IsAdminOrSelf(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_superuser or user == view.user


auto_schema_kwargs = {
    "responses": {
        status.HTTP_200_OK:
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties=OrderedDict((
                    ("key", openapi.Schema(type=openapi.TYPE_STRING, example="value")),
                ))
            )
    }
}  # yapf: disable


@method_decorator(swagger_auto_schema(**auto_schema_kwargs), name="get")
@method_decorator(swagger_auto_schema(**auto_schema_kwargs), name="put")
@method_decorator(swagger_auto_schema(**auto_schema_kwargs), name="patch")
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API to retrive/update a specific profile; Even though all profiles are output
    as part of the UserView, this allows the client to access a profile directly.
    """

    permission_classes = [IsAuthenticated, IsAdminOrSelf]

    @cached_property
    def user(self):
        user_id = self.kwargs["user_id"]
        user = get_object_or_404(get_user_model(), uuid=user_id)
        return user

    @swagger_fake(serializers.Serializer)
    def get_serializer_class(self):
        obj = self.get_object()
        return obj.get_serializer_class()

    @swagger_fake(None)
    def get_object(self):
        # UserProfileView uses fk related_name to specify an object,
        # rather than the standard lookup_field/lookup_url_kwarg

        try:
            profile_name = self.kwargs["profile_name"]
            profile_obj = getattr(self.user, profile_name)
        except Exception as e:
            raise NoMatchingProfileException()

        return profile_obj
