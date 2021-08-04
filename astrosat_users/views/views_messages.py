from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import decorators
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property

from rest_framework import generics, mixins, viewsets
from rest_framework.permissions import IsAuthenticated, BasePermission

from django_filters import rest_framework as filters

from astrosat.decorators import swagger_fake
from astrosat.views import BetterBooleanFilter

from astrosat_users.models import Message
from astrosat_users.serializers import MessageSerializer


class IsAdminOrSelf(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_superuser or user == view.user


class MessageFilterSet(filters.FilterSet):
    class Meta:
        model = Message
        fields = [
            "read",
            "archived",
        ]

    read = BetterBooleanFilter()
    archived = BetterBooleanFilter()


@method_decorator(name="get_object", decorator=swagger_fake(None))
class MessageViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):

    filter_backends = (filters.DjangoFilterBackend, )
    filterset_class = MessageFilterSet
    permission_classes = [IsAuthenticated, IsAdminOrSelf]
    serializer_class = MessageSerializer

    @cached_property
    def user(self):
        user_id = self.kwargs["user_id"]
        user = get_object_or_404(get_user_model(), uuid=user_id)
        return user

    @swagger_fake(Message.objects.none())
    def get_queryset(self):
        return self.user.messages.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if getattr(self, "swagger_fake_view", False):
            context["user"] = None
        else:
            context["user"] = self.user
        return context
