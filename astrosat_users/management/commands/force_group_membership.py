from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """
    Allows me to force a user to be members of the specified groups.
    """

    help = "Force user membership to the specified groups."

    def add_arguments(self, parser):

        parser.add_argument(
            "--username",
            required=True,
            dest="username",
            help="The username to verify."
        )

        parser.add_argument(
            "--groups",
            required=True,
            dest="group_names",
            nargs="*",
            help="The names of groups to join."
        )

    def handle(self, *args, **options):

        username = options["username"]
        group_names = options["group_names"]

        try:
            UserModel = get_user_model()
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            msg = f"Unable to find user '{username}'."
            raise CommandError(msg)

        groups = []
        for group_name in group_names:
            try:
                groups.append(Group.objects.get(name__iexact=group_name))
            except Group.DoesNotExist:
                msg = f"unable to find group '{group_name}'."
                raise CommandError(msg)

        user.groups.add(*groups)
