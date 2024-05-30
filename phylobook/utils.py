""" Holds utility functions that are needed across the project """

import logging
logger = logging.getLogger("app")

from phylobook.utils_early import get_request_object


def current_user():
    """ Get the current user without the request object """
    return get_request_object().user