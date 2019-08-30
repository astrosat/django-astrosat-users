from django.core.management.base import BaseCommand, CommandError
from allauth.account.models import EmailAddress

from astrosat_users.models import User


class Command(BaseCommand):
    """
    Allows me to force a user to be approved.
    """

    help = "Force approval of a user"

    def add_arguments(self, parser):

        parser.add_argument(
            "--username",
            required=True,
            dest="username",
            help="The username to approve.",
        )

    def handle(self, *args, **options):

        username = options["username"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            msg = f"Unable to find user '{username}'."
            raise CommandError(msg)

        if not user.is_approved:
            user.is_approved = True
            user.save()
