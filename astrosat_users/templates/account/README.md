The allauth templates that have changed for astrosat_users go here.

b/c of the way that TEMPLATES["DIRS"] & TEMPLATES["OPTIONS"]["loaders"] is setup in settings, Django will 1st look here and then fall back to using the default templates in "allauth/templates/accounts"

- base.html - ensures that I use the astrosat look-and-feel
- verification_email_sent.html & verified_email_required.html - adds the address that the verification link was sent to
