from random import shuffle

from allauth.account.adapter import get_adapter


def get_adapter_from_response(response):
    """
    Get the adapter being used by a particular test.
    """
    request = response.wsgi_request
    adapter = get_adapter(request)
    return adapter


def shuffle_string(string):
    """
    Mixes up a string. Useful for generating invalid passwords, usernames, etc.
    """
    string_list = list(string)
    shuffle(string_list)
    return "".join(string_list)
