from django.contrib.auth import get_user_model
from django.contrib.auth.management.commands import createsuperuser
from django.core.management.base import BaseCommand, CommandError


class Command(createsuperuser.Command):
    """
    Creates a superuser with the given password.
    Builds upon the existing createsuperuser command.
    (derived from https://github.com/adamcharnock/swiftwind-heroku/blob/master/swiftwind_heroku/management/commands/create_superuser_with_password.py)
    """

    help = "Creates a superuser with the given password."

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            "--password",
            dest="password",
            default=None,
            help="Specifies the password for the superuser.",
        )

    def handle(self, *args, **options):

        options['interactive'] = False  # this command is not interactive (wouldn't be much point)

        password = options.get('password')
        username = options.get('username')

        if password and not username:
            raise CommandError("--username is required if specifying --password")

        super(Command, self).handle(*args, **options)

        if password:
            UserClass = get_user_model()
            user = UserClass.objects.get(**{UserClass.USERNAME_FIELD: username})
            user.set_password(password)
            user.save()
