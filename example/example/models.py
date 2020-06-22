from django.db import models
from django.utils.translation import gettext_lazy as _

from astrosat_users.fields import UserProfileField


class ExampleProfile(models.Model):
    """
    A silly user profile, just for testing.
    """

    class Meta:
        verbose_name = "Example Profile"
        verbose_name_plural = "Example Profiles"

    user = UserProfileField(
        related_name="example_profile",
        serializer_class="example.serializers.ExampleProfileSerializer",
    )

    # some silly fields for playing w/ profiles...
    age = models.IntegerField(blank=True, null=True, help_text=_("Age in years."))
    height = models.FloatField(
        blank=True, null=True, help_text=_("Height in centimeters.")
    )
    weight = models.FloatField(
        blank=True, null=True, help_text=_("Weight in kilograms.")
    )

    @property
    def body_mass_index(self):
        if self.weight and self.height:
            return self.weight / ((self.height / 100) ** 2)
        return None

    def __str__(self):
        return str(self.user)
