from django.contrib.auth.models import BaseUserManager
from django.db import models


# Using a custom QuerySet _and_ a custom Manager may seem needlessly complicated.  But I can't just use
# "QuerySet.as_manager()" w/ AbstractUser b/c I also need to override create_user & create_superuser.
# (as per https://docs.djangoproject.com/en/2.2/topics/auth/customizing/#writing-a-manager-for-a-custom-user-model)

class UserQuerySet(models.QuerySet):

    def active(self):
        return self.filter(is_active=True)

    def approved(self):
        return self.filter(is_approved=True)


class UserManager(BaseUserManager):

    # chainable methods...

    def get_queryset(self):
        return UserQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def approved(self):
        return self.get_queryset().approved()

    # special user methods...

    def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not username:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_approved', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('is_approved') is not True:
            raise ValueError('Superuser must have is_approved=True.')

        return self._create_user(username, email, password, **extra_fields)
