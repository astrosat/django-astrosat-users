Translations
============

Translations will be placed in this folder when running::

    python manage.py makemessages  --locale=<LOCALE_CODE>

Edit the `django.po` file as needed

After that run::

    python manage.py compilemessages

NOTE: LANGUAGES (defined in settings.py) use 'en-gb' format, while LOCALES (used in the above command) use 'en_GB' format
(as per https://docs.djangoproject.com/en/2.2/ref/utils/#django.utils.translation.to_locale)