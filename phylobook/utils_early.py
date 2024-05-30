""" Holds utils that need to be loaded early.  Can't contain import from Models or Managers """

import logging
log = logging.getLogger("app")

import inspect

from django.http import HttpRequest


def get_request_object() -> HttpRequest:
    """ Get the request object from the call stack """

    frame = None

    try:
        for f in inspect.stack()[1:]:
            frame = f[0]
            code = frame.f_code
            if (code.co_varnames and code.co_varnames[0] == "request" or code.co_varnames[:2] == ("self", "request")):
                if "request" in frame.f_locals and isinstance(frame.f_locals["request"], HttpRequest):
                    return frame.f_locals['request']
    finally:
        del frame