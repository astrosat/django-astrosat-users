from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


# TODO: SHOULD ROLES BE COMPOSABLE
# R3 = R2 + R1 (means Role3 inherits Role2's permissions & Role1's permissions, plus any of its own)
# ?


class UserRoleManager(models.Manager):
    """
    This manager lets me deserialize using natural_keys
    (this allows me to use fixtures w/out having to hard-code pks)
    """

    def get_by_natural_key(self, name):
        return self.get(name=name)


class UserRole(models.Model):

    """
    We want something way more general than the built-in django groups/permissions system.
    We also want something that can be updated easily in the db via admin/backend/api.
    """

    class Meta:
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"

    objects = UserRoleManager()

    name = models.CharField(unique=True, blank=False, null=False, max_length=255)
    description = models.TextField(blank=True, null=True)

    permissions = models.ManyToManyField(
        "UserPermission", related_name="roles", blank=True
    )

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)


class UserPermissionManager(models.Manager):
    """
    This manager lets me deserialize using natural_keys
    (this allows me to use fixtures w/out having to hard-code pks)
    """

    def get_by_natural_key(self, name):
        return self.get(name=name)


class UserPermission(models.Model):
    class Meta:
        verbose_name = "User Permission"
        verbose_name_plural = "User Permissions"

    objects = UserPermissionManager()

    name = models.CharField(
        validators=[
            RegexValidator(
                regex="^[a-z0-9-_]+$",
                message="Permission must have no spaces, capital letters, or funny characters.",
                code="invalid_name",
            )
        ],
        unique=True,
        blank=False,
        null=False,
        max_length=255,
    )
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)
