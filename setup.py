import os
from setuptools import find_packages, setup


# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

README = open("README.md").read()

# dynamically compute the version, etc...
author = __import__("astrosat_users").__author__
title = __import__("astrosat_users").__title__
version = __import__("astrosat_users").__version__

dependencies = [
    "django~=3.0",  # django, duh
    "django-allauth>=0.39",  # users
    "djangorestframework~=3.0",  # api
    "dj-rest-auth",  # api-users
    "django-rest-knox",  # tokens
    "zxcvbn",  # paswords
]

setup(
    name=title,
    version=version,
    author=author,
    description="Behold Django-Astrosat-Users!",
    long_description=README,
    url="https://github.com/astrosat/django-astrosat/users/",
    install_requires=dependencies,
    packages=find_packages(exclude=["example"]),
    include_package_data=True,
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 3.0  ",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
