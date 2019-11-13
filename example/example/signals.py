from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from .models import ExampleProfile


def post_save_user_hander(sender, *args, **kwargs):
    """
    If a User has just been created,
    then the corresponding profile must also be created.
    """

    created = kwargs.get("created", False)
    instance = kwargs.get("instance", None)
    if created and instance:
        ExampleProfile.objects.create(user=instance)


post_save.connect(
    post_save_user_hander,
    sender=get_user_model(),
    dispatch_uid="post_save_user_handler",
)
