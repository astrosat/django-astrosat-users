from django.core.management.base import BaseCommand, CommandError

from astrosat_users.models import User


class Command(BaseCommand):
    """
    Allows me to force a user to have accepted terms & conditions.
    """

    help = "Force term acceptance of a user"

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

        if not user.accepted_terms:
            user.accepted_terms = True
            user.save()
