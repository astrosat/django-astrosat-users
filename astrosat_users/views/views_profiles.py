from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from rest_framework import generics
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated, BasePermission

from astrosat.decorators import swagger_fake


class NoMatchingProfileException(APIException):
    status_code = 400
    default_detail = "Unable to find a profile for the given user "
    default_code = "no_matching_profile"


class IsAdminOrSelf(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_superuser or user == view.user


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API to retrive/update a specific profile;
    Even though all user profiles are output along w/ a user,
    that is a readonly-field.
    """

    permission_classes = [IsAuthenticated, IsAdminOrSelf]

    @cached_property
    def user(self):
        user_id = self.kwargs["user_id"]
        user = get_object_or_404(get_user_model(), uuid=user_id)
        return user

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

        # self.check_object_permissions(self.request, profile_obj)

        return profile_obj
