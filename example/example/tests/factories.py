import factory
from factory.faker import (
    Faker as FactoryFaker,
)  # note I use FactoryBoy's wrapper of Faker

from django.db.models.signals import post_save

from astrosat_users.tests.factories import (
    UserFactory as AstrosatUserFactory,
    UserRoleFactory,
    UserPermissionFactory,
)

from example.models import ExampleProfile


class ExampleProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExampleProfile

    age = FactoryFaker("pyint", min_value=1, max_value=100)
    height = FactoryFaker("pyfloat", min_value=150.0, max_value=215.0)
    weight = FactoryFaker("pyfloat", min_value=20.0, max_value=150.0)

    # "example_profile=None" means that if I create an ExampleProfile explicitly, another profile won't be created
    # (it disables the RelatedFactory below)
    user = factory.SubFactory(
        "example.tests.factories.UserFactory", example_profile=None
    )


@factory.django.mute_signals(
    post_save
)  # prevent signals from trying to create a profile outside of this factory
class UserFactory(AstrosatUserFactory):

    # "user" means that if I create a UserFactory explicitly, another user won't be created
    # (it disables the SubFactory above)
    example_profile = factory.RelatedFactory(ExampleProfileFactory, "user")
