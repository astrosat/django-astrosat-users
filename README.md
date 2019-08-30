# django-astrosat-users

## quick start

 1. in the project you want to use it type:
`pipenv install -e git+https://github.com/astrosat/django-astrosat-users.git@master#egg=django-astrosat`

 2. add "astrosat_users" to your INSTALLED_APPS settings like this:
```
     INSTALLED_APPS = [
         ...
         'astrosat_users',
         ...
    ]
```
 3. include the astrosat URLconf in your project "urls.py" like this:
 ```
	 path("", include("astrosat_users.urls")
 ```
 4. you may also want to override the templates:
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

 5. run `python manage.py migrate` to create the astrosat models.

 6. profit!


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

note that "django-astrosat-users/examples/Pipfile" was created using `pipenv install -e ..`; this uses a pointer to "django-astrosat-users/setup.py" in the virtual environment and creates a entry like [packages.ed0a5ba]; if the distribution changes just run `pipenv update ed0a5ba`, otherwise code changes should just be picked up b/c  of the `-e` flag.

note note that django-astrosat-users requires django-astrosat-core; to enable this I ran `pipenv install -e git+https://github.com/astrosat/django-astrosat-core.git@master#egg=django-astrosat-core`

note note note that when things go wrong, I tend to get this error: "LookupError: No installed app with label 'admin'."

FYI - deployments may care about https://docs.pipenv.org/en/latest/advanced/#injecting-credentials-into-pipfiles-via-environment-variables

FYI - sometimes pipenv waits for pip to get input from stdin (like w/ github repos); to get around this set `PIPENV_NOSPIN=1` as per https://github.com/pypa/pipenv/issues/3770
