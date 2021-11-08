"""
WSGI config for phylobook project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os
import time
import traceback
import signal
import sys

from django.core.wsgi import get_wsgi_application

sys.path.append('/var/www/vhosts/phylobook')
# adjust the Python version in the line below as needed
#sys.path.append('/var/www/vhosts/phylobook/venv/lib/python3.7/site-packages')
sys.path.append('/opt/venv/lib/python3.8/site-packages')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phylobook.settings')

try:
    application = get_wsgi_application()
except Exception:
    # Error loading applications
    if 'mod_wsgi' in sys.modules:
        traceback.print_exc()
        os.kill(os.getpid(), signal.SIGINT)
        time.sleep(2.5)


# -sys.path.append('/var/www/vhosts/tree_project')
# +sys.path.append('/var/www/vhosts/phylobook')
# # adjust the Python version in the line below as needed
# -sys.path.append('/var/www/vhosts/tree_project/vvenv/lib/python3.6/site-packages')
# +sys.path.append('/var/www/vhosts/phylobook/venv/lib/python3.7/site-packages')
#
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phylobook.settings')