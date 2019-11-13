import os
from setuptools import find_packages, find_namespace_packages, setup

with open(os.path.join(os.path.dirname(__file__), "README.md")) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

# dynamically compute the version, etc....
author = __import__("astrosat_users").__author__
title = __import__("astrosat_users").__title__
version = __import__("astrosat_users").__version__

install_requires = [
    # django, duh
    "django>=2.2",
    # api
    "djangorestframework>=3.9",
    # users
    "django-allauth>=0.39",
    # api-users
    "django-rest-auth>=0.9",
]


setup(
    name=title,
    version=version,
    author=author,
    url="https://github.com/astrosat/django-astrosat-users",
    description="Behold Django-Astrosat-Users!",
    long_description=README,
    install_requires=install_requires,
    packages=find_packages(exclude=["example"]),
    include_package_data=True,
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
