from django.conf import settings
from django.shortcuts import render
from django.utils.html import mark_safe


def text_view(request, text=None, title=None):
    """
    provides a generic way to render any old text in a template
    (used for when a user is disabled, or unapproved, or unverified, etc.)
    """
    context = {"text": mark_safe(text), "title": title or settings.PROJECT_NAME}
    return render(request, "astrosat_users/text.html", context)
