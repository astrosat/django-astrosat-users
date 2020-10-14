from typing import Any, Sequence

import factory
from factory.faker import (
    Faker as FactoryFaker,
)  # note I use FactoryBoy's wrapper of Faker

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.text import slugify

from astrosat.tests.providers import PrettyLoremProvider
from astrosat.tests.utils import optional_declaration

from allauth.account.models import EmailAddress
from astrosat_users.models import User, UserRole, UserPermission, Customer
from astrosat_users.models.models_customers import CompanyTypes, CustomerType
from astrosat_users.tests.utils import *

FactoryFaker.add_provider(PrettyLoremProvider)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ["email"]

    email = FactoryFaker("email")
    name = FactoryFaker("name")
    description = optional_declaration(FactoryFaker("sentence", nb_words=10), chance=50)
    requires_customer_registration_completion = False
    accepted_terms = True
    is_approved = False

    @factory.lazy_attribute
    def username(self):
        return self.email.split("@")[0]

    @factory.lazy_attribute
    def avatar(self):
        return SimpleUploadedFile(
            name=f"{self.username}_avatar.png",
            content=b"I am a fake image",
            content_type="image/png",
        )

    @factory.post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):
        password = generate_password()
        self.raw_password = (
            password  # the instance has a "raw_password" variable to use in tests
        )
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
            emailaddress = EmailAddressFactory(
                user=self, email=self.email, primary=True, verified=False
            )


class EmailAddressFactory(factory.django.DjangoModelFactory):
    """
    I don't really use this on its own.  Instead I create an (unverified) email address when a user is created above.
    This is done by default when I create a user via the registration views.  But if I am bypassing that,
    I still need an EmailAddress instance to exist.
    """

    class Meta:
        model = EmailAddress

    verified = False
    primary = True
    email = FactoryFaker("email")
    user = factory.SubFactory(UserFactory, emailaddress_set=None)


class UserRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserRole

    description = optional_declaration(FactoryFaker("sentence", nb_words=10), chance=50)

    @factory.lazy_attribute_sequence
    def name(self, n):
        word = FactoryFaker("word").generate()
        return f"{word.title()}{n}Role"

    @factory.post_generation
    def permissions(self, create: bool, extracted: Sequence[Any], **kwargs):
        N_PERMISSIONS = 2
        if not create:
            return

        if extracted:
            for permission in extracted:
                self.permissions.add(permission)

        else:
            for _ in range(N_PERMISSIONS):
                permission = UserPermissionFactory()
                self.permissions.add(permission)


class UserPermissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserPermission

    description = optional_declaration(FactoryFaker("sentence", nb_words=10), chance=50)

    @factory.lazy_attribute_sequence
    def name(self, n):
        words = FactoryFaker("words", nb=2).generate()
        return f"can_{'_'.join(words)}_{n}"


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    customer_type = CustomerType.MULTIPLE

    name = FactoryFaker("name")
    official_name = FactoryFaker("name")
    company_type = CompanyTypes.NON_PROFIT
    registered_id = factory.LazyAttributeSequence(
        lambda o, n: f"{slugify(o.name)}-{n}"
    )
    description = FactoryFaker("text")
    url = FactoryFaker("url")

    @factory.lazy_attribute
    def logo(self):
        return SimpleUploadedFile(
            name=f"{self.name}_logo.png",
            content=b"I am a fake image",
            content_type="image/png",
        )
