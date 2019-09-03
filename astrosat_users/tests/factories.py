from typing import Any, Sequence

import factory
from factory.faker import Faker as FactoryFaker  # note I use FactoryBoy's wrapper of Faker

from astrosat.tests.providers import GeometryProvider, ValidatedProvider
from astrosat.tests.utils import optional_declaration

from allauth.account.models import EmailAddress
from astrosat_users.models import User


FactoryFaker.add_provider(GeometryProvider)
FactoryFaker.add_provider(ValidatedProvider)


class UserFactory(factory.DjangoModelFactory):

    class Meta:
        model = User
        django_get_or_create = ["username"]

    username = FactoryFaker("user_name")
    email = FactoryFaker("email")
    name = FactoryFaker("name")
    description = optional_declaration(
        FactoryFaker("sentence", nb_words=10),
        chance=50
    )
    is_approved = False

    # change_password =

    @factory.post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):
        password = FactoryFaker(
            "password",
            length=20,
            special_chars=True,
            digits=True,
            upper_case=True,
            lower_case=True,
        ).generate(extra_kwargs={})
        self.raw_password = password  # the instance has a "raw_password" object for me to use in tests
        self.set_password(password)

    @factory.post_generation
    def emailaddress_set(self, create: bool, extracted: Sequence[Any], **kwargs):

        if not create:
            return

        if extracted:
            # I am very unlikely to be here, creating loads of emailaddresses
            for emailaddress in extracted:
                self.emailaddress_set.add(emailaddress)
        else:
            emailaddress = EmailAddressFactory(user=self, email=self.email, primary=True, verified=False)


class EmailAddressFactory(factory.DjangoModelFactory):
    """
    I don't really use this on its own.  Instead I create an (unverified) email address when a user is created above.
    This is done by default when I create a user via the registration views.  But if I am bypassing that,
    I still need an EmailAddress instance to exist.
    (see for example: "example.tests.test_integration.py#TestAPIViews.test_login_unverified")
    """
    class Meta:
        model = EmailAddress


    verified = False
    primary = True
    email = FactoryFaker("email")
    user = factory.SubFactory(UserFactory, emailaddress_set=None)