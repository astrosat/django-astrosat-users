from django import template
from django.utils.html import mark_safe

import astrosat_users

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
