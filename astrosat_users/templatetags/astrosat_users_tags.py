from django import template
from django.utils.html import mark_safe

import astrosat_users
from astrosat_users.models import User
from astrosat_users.profiles import get_profile_qs


register = template.Library()


##################
# some constants #
##################

@register.simple_tag
def astrosat_users_title():
    return mark_safe(astrosat_users.__title__)


@register.simple_tag
def astrosat_users_author():
    return mark_safe(astrosat_users.__author__)


@register.simple_tag
def astrosat_users_version():
    return mark_safe(astrosat_users.__version__)


#####################
# some other things #
#####################

@register.simple_tag
def users():
    return User.objects.filter(is_active=True)

@register.simple_tag
def profiles():
    return get_profile_qs()
