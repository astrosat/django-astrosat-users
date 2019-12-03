# django-astrosat-users

## quick start

1.  in the project you want to use it type:
    `pipenv install -e git+https://github.com/astrosat/django-astrosat-users.git@master#egg=django-astrosat`

2.  add "astrosat_users" to your INSTALLED_APPS settings like this:

```
     INSTALLED_APPS = [
         ...
         'astrosat_users',
         ...
    ]
```

3.  add lots of settings; look at "astrosat_users/conf/settings.py" to see what to add

4.  include the astrosat URLconf in your project "urls.py" like this:

```
 path("", include("astrosat_users.urls")
```

5.  you may also want to override the templates:

```
TEMPLATES = [
   {
       ...
       'DIRS': [
           os.path.join(BASE_DIR, "wherever/you/put/templates"),
       ],
       'OPTIONS': {
           'loaders': [
               'django.template.loaders.filesystem.Loader',
               'django.template.loaders.app_directories.Loader',
           ],
       ...
]
```

(to use the built-in astrosat templates, use something like `os.path.join(os.path.dirname(importlib.import_module("astrosat_users").__file__), "templates")`)

6.  run `python manage.py migrate` to create the astrosat models.

7.  profit!

## developing

django-astrosat-users comes w/ an example project to help w/ developing/testing

1. `git clone <repo> django-astrosat-users`
2. `cd django-astrosat-users/example`
3. activate virtual environments as desired
4. `pipenv install`
5. `python manage.py makemigrations && python manage.py migrate` as needed
6. `python manage.py collectstatic --noinput` as needed
7. `pytest` and enjoy
8. `python manage.py runserver` goto "http://localhost:8000" and enjoy

note that the reference to django-astrosat-core in the Pipfile was created with: `pipenv install -e git+git@github.com/astrosat/django-astrosat-core.git@master#egg=django-astrosat-core`. This uses SSH to connect to github. Appropriate security settings should be used in your project. This will fetch the latest commit on the master branch and use that hash as the key in Pipfile.lock. This means that if django-astrosat-core changes, the Pipfile.lock must be rebuilt in order to use the latest version.

note that the reference to django-astrosat-users in the Pipfile was created with: `pipenv install -e ..`. This looks for the "setup.py" file in the parent directory. If the distribution changes just run `pipenv update django-astrosat-users`, otherwise code changes should just be picked up b/c of the "-e" flat.

FYI - sometimes pipenv waits for pip to get input from stdin (like w/ github repos); to get around this set `PIPENV_NOSPIN=1` as per https://github.com/pypa/pipenv/issues/3770

## notes

### authentication:

DRF BasicAuthentication is disabled (b/c it's a security risk)
DRF supports SessionAuthentication (using CSRF token)
DRF supports TokenAuthentication;
...and I use KnoxTokens for that.

This requires the following header:
"Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
In each view, I can check request.auth to see if it is SessionAuthentication or TokenAuthentication

in drf-yasg I can authorize by passing "Token <key>" to the textbox after being sure to add this to settings:

```
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Token Authentication': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': escape("Enter 'Token <key>'"),
        }
    }
}
```

### sending emails:

`AccountAdapter.get_email_confirmation_url()` will give a different url based on whether @is_api is `True` or `False`. If `False`, "allauth" works as expected. If `True`, it uses the value of `settings.ACCOUNT_CONFIRM_EMAIL_CLIENT_URL` (which ought to be a format string). The client needs to get that request and then parse the key and POST it to `reverse("rest_verify_email")` ("/api/authentication/registration/verify-email")

The same basic logic holds for resetting passwords.
