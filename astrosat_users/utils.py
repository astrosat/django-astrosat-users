from knox.models import AuthToken

from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode


def create_knox_token(token_model, user, serializer):
    instance, token = AuthToken.objects.create(user=user)
    # return token.token_key
    # token = AuthToken.objects.create(user=user)
    return (instance, token)


def rest_encode_user_pk(user):
    return urlsafe_base64_encode(force_bytes(user.pk))


def rest_decode_user_pk(encoded_user):
    return force_text(urlsafe_base64_decode(encoded_user))
