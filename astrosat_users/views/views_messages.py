from django.conf import settings
from django.shortcuts import render
from django.utils.html import mark_safe


def message_view(request, message=None, title=None):
    """
    provides a generic way to render any old message in a template
    (used for when a user is disabled, or unapproved, or unverified, etc.)
    """
    context = {
        "message": mark_safe(message),
        "title": title or settings.PROJECT_NAME
    }
    return render(request, "astrosat_users/message.html", context)
