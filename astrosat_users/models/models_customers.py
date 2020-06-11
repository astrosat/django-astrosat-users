from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from astrosat_users.signals import customer_added_user, customer_removed_user


def customer_logo_path(instance, filename):
    return f"customers/{instance}/{filename}"


class CustomerType(models.TextChoices):
    SINGLE = "SINGLE", _("Single")
    MULTIPLE = "MULTIPLE", _("Multiple")


class CustomerUserType(models.TextChoices):
    MANAGER = "MANAGER", _("Manager")
    MEMBER = "MEMBER", _("Member")


class CustomerUserStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active")
    PENDING = "PENDING", _("Pending")


class CustomerQuerySet(models.QuerySet):
    def single(self):
        return self.filter(customer_type=CustomerType.SINGLE)

    def multiple(self):
        return self.filter(customer_type=CustomerType.MULTIPLE)

# TODO: FK INSTEAD OF M2M; REAL MODEL INSTEAD OF THROUGH MODEL
# TODO: abstract + 2 child classes

class Customer(models.Model):
    class Meta:
        # abstract = True
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    objects = CustomerQuerySet.as_manager()

    roles = models.ManyToManyField("UserRole", related_name="customers", blank=True)

    is_active = models.BooleanField(default=True)

    _users = models.ManyToManyField(
        # I tend not to use this field directly (hence the "_" prefix)
        # instead I use the properties below to access the Through Model
        settings.AUTH_USER_MODEL,
        through="CustomerUser",
        related_name="customers",
    )

    customer_type = models.CharField(
        max_length=64, choices=CustomerType.choices, default=CustomerType.MULTIPLE
    )

    name = models.SlugField(unique=True, blank=False, null=False)
    title = models.CharField(max_length=128, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    logo = models.FileField(upload_to=customer_logo_path, blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    #     max_licenses = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name

    @property
    def users(self):
        return self._users.through.objects.filter(customer=self)

    @property
    def managers(self):
        return self.users.managers()

    @property
    def members(self):
        return self.users.members()


#     @property
#     def n_licenses(self):
#         return self.users.count()

#     def add_user(self, user, customer_user_type=CustomerUserType.MEMBER):
#         customer_added_user.send(sender=self, user=user)

#     def remove_user(self, user):
#         assert not user.is_manager
#         customer_removed_user.send(sender=self, user=user)


class CustomerUserQuerySet(models.QuerySet):
    def managers(self):
        return self.filter(customer_user_type=CustomerUserType.MANAGER)

    def members(self):
        return self.filter(customer_user_type=CustomerUserType.MEMBER)

    def active(self):
        return self.filter(customer_user_status=CustomerUserStatus.ACTIVE)

    def pending(self):
        return self.filter(customer_user_status=CustomerUserStatus.PENDING)


class CustomerUser(models.Model):
    # a "through" model for the relationship between customers & users

    objects = CustomerUserQuerySet.as_manager()

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    customer_user_type = models.CharField(
        max_length=64, choices=CustomerUserType.choices
    )
    customer_user_status = models.CharField(
        max_length=64, choices=CustomerUserStatus.choices
    )


# class CustomerInvitation(models.Model):
#     pass
