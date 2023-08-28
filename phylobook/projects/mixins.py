import logging
log = logging.getLogger('app')

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden


class LoginRequredSimpleErrorMixin(LoginRequiredMixin):
    """ LoginRequiredMixin that returns the error message with no HTML, for use with AJAX """

    def handle_no_permission(self):
        """ Return the error message with no HTML."""

        message = self.permission_denied_message or "You seem to have been logged out at some point."

        log.warning(f" Got login required error on an AJAX request ({self.request.build_absolute_uri()}): {message}")
        return HttpResponseForbidden(message)