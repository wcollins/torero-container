"""WSGI config for torero_ui project."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "torero_ui.settings")

application = get_wsgi_application()