from django.contrib.auth.backends import RemoteUserBackend


class VVRemoteUserBackend(RemoteUserBackend):
    """
    This backend is to be used in conjunction with the ``RemoteUserMiddleware``
    found in the middleware module of this package, and is used when the server
    is handling authentication outside of Django.

    By default, the ``authenticate`` method creates ``User`` objects for
    usernames that don't already exist in the database.  Subclasses can disable
    this behavior by setting the ``create_unknown_user`` attribute to
    ``False``.  VVRemoteUserBackend sets create_unknown_user to False.
    """

    # Create a User object if not already in the database?
    create_unknown_user = False
