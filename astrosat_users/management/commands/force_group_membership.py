from itertools import chain

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
            nargs="+",
            help="The names of groups to join."
        )

        parser.add_argument(
            "--regex",
            dest="is_regex",
            action="store_true",
            help="Whether or not to treat the group_names as regexs",
        )

    def handle(self, *args, **options):

        username = options["username"]
        group_names = options["group_names"]
        is_regex = options["is_regex"]

        try:
            UserModel = get_user_model()
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            msg = f"Unable to find user '{username}'."
            raise CommandError(msg)

        if is_regex:
            filter_expr = "name__iregex"
        else:
            filter_expr = "name__iexact"

        groups = []
        for group_name in group_names:
            filtered_groups = Group.objects.filter(**{filter_expr: group_name})
            if not filtered_groups.exists():
                msg = f"Unable to find any groups matching '{group_name}'"
                raise CommandError(msg)
            groups.append(filtered_groups)

        user.groups.add(*chain.from_iterable(groups))
        self.stdout.write(
            f"successfully assigned user '{user}' to groups: '{', '.join([group.name for group in chain.from_iterable(groups)])}'."
        )
