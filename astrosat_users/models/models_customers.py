import uuid

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


class Customer(models.Model):
    class Meta:
        # abstract = True
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    objects = CustomerQuerySet.as_manager()

    roles = models.ManyToManyField("UserRole", related_name="customers", blank=True)

    is_active = models.BooleanField(default=True)

    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="CustomerUser", related_name="customers"
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

    #     @property
    #     def n_licenses(self):
    #         return self.users.count()

    def add_user(self, user, **kwargs):
        user, created = self.customer_users.add_user(user, **kwargs)
        if created:
            customer_added_user.send(sender=self, user=user)
        return (user, created)

    # def remove_user(self, user):
    #     assert not user.is_manager
    #     self.customer_users.remove_user(user)
    #     customer_removed_user.send(sender=self, user=user)

    def delete(self, *args, **kwargs):
        """
        When a customer is deleted, delete the corresponding logo storage.
        """
        if self.logo:
            logo_name = self.logo.name
            logo_storage = self.logo.storage
            if logo_storage.exists(logo_name):
                logo_storage.delete(logo_name)

        return super().delete(*args, **kwargs)


class CustomerUserManager(models.Manager):
    def add_user(self, user, **kwargs):
        defaults = {
            "customer_user_type": kwargs.get("type", CustomerUserType.MEMBER),
            "customer_user_status": kwargs.get("status", CustomerUserStatus.PENDING),
        }
        return self.update_or_create(user=user, defaults=defaults)


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

    objects = CustomerUserManager.from_queryset(CustomerUserQuerySet)()

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="customer_users"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_users",
    )

    customer_user_type = models.CharField(
        max_length=64, choices=CustomerUserType.choices
    )
    customer_user_status = models.CharField(
        max_length=64, choices=CustomerUserStatus.choices
    )

    def __str__(self):
        return f"{self.customer}: {self.user}"


# class CustomerInvitation(models.Model):
#     pass
