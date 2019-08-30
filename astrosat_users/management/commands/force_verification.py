from django.core.management.base import BaseCommand, CommandError
from allauth.account.models import EmailAddress

from astrosat_users.models import User


class Command(BaseCommand):
    """
    Allows me to force a user's primary email address to be verified,
    as if they had replied to the email confirmation message.
    """

    help = "Force verification of a user's primary email address."

    def add_arguments(self, parser):

        parser.add_argument(
            "--username",
            required=True,
            dest="username",
            help="The username to verify.",
        )

    def handle(self, *args, **options):

        username = options["username"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            msg = f"Unable to find user '{username}'."
            raise CommandError(msg)

        if not user.is_verified:
            user.verify()
